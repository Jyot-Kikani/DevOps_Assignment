import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
import json
import os
import time
from uuid import uuid4
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import DBAPIError
from stellar_journey.app import app
from stellar_journey.db import journeys
from stellar_importer.pipeline import load_catalog
from stellar_importer.maintenance import retention
from import_support import ROOT,CSV,fixture_manifest
from http_support import live_service


@pytest.fixture
def journey_service(tmp_path,monkeypatch):
    manifest = fixture_manifest(tmp_path)
    sid = json.loads(manifest.read_text())["snapshot_id"]
    load_catalog(CSV,manifest,activate=True)
    monkeypatch.setenv("CATALOG_SNAPSHOT_ID",sid)
    monkeypatch.setenv("APP_ENV","ci")
    with live_service("catalog",sid,tmp_path) as (base,log):
        monkeypatch.setenv("CATALOG_INTERNAL_URL",base)
        with TestClient(app) as client:
            yield client,sid,base,log


def body(sid):
    return {"snapshot_id":sid,"origin_id":"sun","destination_id":"5853498713190525696","speed_fraction_c":0.1}


def test_estimate_http_oracle_request_ids_and_validation(journey_service):
    client,sid,base,log = journey_service
    assert client.get("/health/ready").status_code==200
    assert client.get("/v1/meta").json()["readiness"] is True
    identifier = "journey-catalog-proof-1"
    response = client.post("/v1/estimate",json=body(sid),headers={"X-Request-ID":identifier})
    assert response.status_code==200,response.text
    result = response.json()
    assert result["origin_position_pc"]==[0,0,0]
    assert result["distance_ly"]==pytest.approx(4.2464,abs=0.0001)
    assert result["duration_julian_years"]==pytest.approx(result["distance_ly"]/0.1)
    assert result["speed_km_s"]==pytest.approx(29979.2458)
    assert result["model_version"]=="constant-speed-v1" and result["assumptions"]
    assert identifier in log.read_text()  # Propagated across a real TCP/HTTP process boundary.
    for speed in (0.001,0.5):
        assert client.post("/v1/estimate",json=body(sid)|{"speed_fraction_c":speed}).status_code==200
    assert client.post("/v1/estimate",json=body(sid)|{"destination_id":"sun"}).status_code==422
    for change in ({"destination_id":5853498713190525696},{"position_pc":[0,0,0]},{"url":"https://example.com"},
                   {"speed_fraction_c":0.0009},{"speed_fraction_c":0.5001},{"speed_fraction_c":True}):
        assert client.post("/v1/estimate",json=body(sid)|change).status_code==422
    assert client.post("/v1/estimate",content='{"broken":',headers={"Content-Type":"application/json"}).status_code==400
    assert client.post("/v1/estimate",content="x"*4097).status_code==400
    assert client.post("/v1/estimate",json=body(sid)|{"destination_id":"999999"}).status_code==404
    assert client.post("/v1/estimate",json=body("unknown")).status_code==404
    assert client.post("/v1/journeys",json=body(sid)).status_code==400


def test_shared_round_trip_idempotency_races_frozen_data_and_conflict(journey_service,tmp_path):
    client,sid,base,_ = journey_service
    payload = body(sid)
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=6) as pool:
        responses = list(pool.map(lambda _:client.post("/v1/journeys",json=payload,headers={"Idempotency-Key":key}),range(6)))
    assert sorted(r.status_code for r in responses)==[200,200,200,200,200,201],[r.text for r in responses]
    first = responses[0].json()
    assert all(r.json()==first for r in responses)
    assert all(r.headers["Location"]=="/v1/journeys/"+first["id"] for r in responses)
    assert client.get(responses[0].headers["Location"]).json()==first
    assert datetime.fromisoformat(first["expires_at"].replace("Z","+00:00"))-datetime.fromisoformat(first["created_at"].replace("Z","+00:00"))==timedelta(days=30)
    assert "idempotency_key" not in first and "request_hash" not in first
    from prometheus_client.parser import text_string_to_metric_families
    metrics = client.get("/metrics")
    assert metrics.status_code==200
    labels = [v for family in text_string_to_metric_families(metrics.text) for sample in family.samples for v in sample.labels.values()]
    assert first["id"] not in labels and key not in labels
    assert client.post("/v1/journeys",json=payload|{"speed_fraction_c":0.2},headers={"Idempotency-Key":key}).status_code==409
    engine = create_engine(os.environ["JOURNEY_DSN"],hide_parameters=True)
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM journey.journeys WHERE idempotency_key=CAST(:k AS uuid)"),{"k":key}).scalar()==1
        fields = set(c.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema='journey' AND table_name='journeys'")).scalars())
    assert not fields.intersection({"ip","email","cookie","user_id","title"})
    for sql in ("UPDATE journey.journeys SET speed_fraction_c=0.2 WHERE id=CAST(:id AS uuid)",
                "DELETE FROM journey.journeys WHERE id=CAST(:id AS uuid)"):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(sql),{"id":first["id"]})
    newer = fixture_manifest(tmp_path)
    load_catalog(CSV,newer,activate=True)
    assert client.get("/v1/journeys/"+first["id"]).json()==first
    engine.dispose()


def test_postgres_rejects_invalid_frozen_record_shapes_and_numbers(journey_service):
    client,sid,_,_ = journey_service
    created = client.post("/v1/journeys",json=body(sid),headers={"Idempotency-Key":str(uuid4())}).json()
    engine = create_engine(os.environ["JOURNEY_DSN"],hide_parameters=True)
    with engine.connect() as c:
        row = dict(c.execute(select(journeys).where(journeys.c.id==__import__("uuid").UUID(created["id"]))).mappings().one())
    for change in ({"origin_position_pc":[]},{"destination_position_pc":[1,2]},
                   {"origin_position_pc":[float("nan"),0,0]},{"distance_pc":float("inf")},
                   {"speed_fraction_c":0.9},{"assumptions":{}},{"origin_id":"1e19"}):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(journeys.insert().values(**(row|{"id":uuid4(),"idempotency_key":uuid4()}|change)))
    engine.dispose()


def test_controlled_clock_expiry_and_real_batched_purge(journey_service):
    client,sid,_,_ = journey_service
    key = str(uuid4())
    created = client.post("/v1/journeys",json=body(sid),headers={"Idempotency-Key":key}).json()
    expires = datetime.fromisoformat(created["expires_at"].replace("Z","+00:00"))
    clock = app.state.clock
    app.state.clock = lambda:expires
    assert client.get("/v1/journeys/"+created["id"]).status_code==410
    assert client.post("/v1/journeys",json=body(sid),headers={"Idempotency-Key":key}).status_code==410
    app.state.clock = lambda:expires+timedelta(days=7)
    assert client.get("/v1/journeys/"+created["id"]).status_code==404
    app.state.clock = clock
    # Seed expired records with their original timestamps; no update or TTL bypass.
    engine = create_engine(os.environ["JOURNEY_DSN"],hide_parameters=True)
    with engine.connect() as c:
        template = dict(c.execute(select(journeys).where(journeys.c.id==__import__("uuid").UUID(created["id"]))).mappings().one())
    original_ids = []
    past = datetime.now(timezone.utc)-timedelta(days=38)
    rows = []
    for _ in range(1001):
        id = uuid4()
        original_ids.append(id)
        rows.append(template|{"id":id,"idempotency_key":uuid4(),"created_at":past,"expires_at":past+timedelta(days=30)})
    with engine.begin() as c:
        c.execute(journeys.insert(),rows)
    result = retention()
    assert result["status"]=="passed" and result["deleted"]>=1001 and result["batch_size"]==1000
    assert client.get("/v1/journeys/"+str(original_ids[0])).status_code==404
    assert client.get("/v1/journeys/"+created["id"]).status_code==200
    engine.dispose()


def test_catalog_retry_total_timeout_mismatch_and_own_db_failure(journey_service):
    client,sid,_,_ = journey_service
    original = app.state.catalog_client
    calls = []
    positions = {"snapshot_id":sid,"items":[{"source_id":"sun","position_pc":[0,0,0]},
                 {"source_id":"5853498713190525696","position_pc":[3,4,0]}]}
    def handle(request):
        calls.append(request)
        if len(calls)==1:
            return httpx.Response(503,json={})
        return httpx.Response(200,json=positions)
    mocked = httpx.AsyncClient(base_url="http://catalog",transport=httpx.MockTransport(handle),follow_redirects=False,trust_env=False)
    app.state.catalog_client = mocked
    try:
        response = client.post("/v1/estimate",json=body(sid),headers={"X-Request-ID":"retry-proof"})
        assert response.status_code==200 and len(calls)==2
        assert response.json()["distance_pc"]==5 and response.json()["duration_julian_years"]==pytest.approx(163.07818885)
        assert all(r.headers["X-Request-ID"]=="retry-proof" for r in calls)
        calls.clear()
        def reset(request):
            calls.append(request)
            raise httpx.ConnectError("fixture reset")
        app.state.catalog_client._transport = httpx.MockTransport(reset)
        assert client.post("/v1/estimate",json=body(sid)).status_code==503 and len(calls)==2
        for status,content,expected in ((503,{},503),(302,{},503),(200,positions|{"snapshot_id":"different"},409),
                (200,{"snapshot_id":sid,"items":[]},503)):
            app.state.catalog_client._transport = httpx.MockTransport(lambda r:httpx.Response(status,json=content,headers={"Location":"http://do-not-follow.invalid"}))
            assert client.post("/v1/estimate",json=body(sid)).status_code==expected
        async def slow(request):
            await asyncio.sleep(4)
            return httpx.Response(200,json=positions)
        app.state.catalog_client._transport = httpx.MockTransport(slow)
        started = time.monotonic()
        assert client.post("/v1/estimate",json=body(sid)).status_code==503
        assert 2.8<=time.monotonic()-started<3.8
        # Catalog failure must not make the healthy Journey process/own DB unready.
        assert client.get("/health/live").status_code==200
        assert client.get("/health/ready").status_code==200
        own = app.state.engine
        app.state.engine = create_engine("postgresql+psycopg://journey_app:invalid@127.0.0.1:1/stellar_journey",hide_parameters=True,connect_args={"connect_timeout":1})
        try:
            response = client.get("/v1/journeys/"+str(uuid4()))
            assert response.status_code==503 and "invalid@" not in response.text
            assert client.post("/v1/journeys",json=body(sid),headers={"Idempotency-Key":str(uuid4())}).status_code==503
            assert client.get("/health/ready").status_code==503
            assert client.get("/health/live").status_code==200
        finally:
            app.state.engine.dispose()
            app.state.engine = own
    finally:
        asyncio.run(mocked.aclose())
        app.state.catalog_client = original
