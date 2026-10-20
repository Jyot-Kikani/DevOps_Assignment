import base64
import hashlib
import json
import math
import os
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, text
from stellar_catalog.app import app
from stellar_common.map_format import decode
from stellar_importer.pipeline import load_catalog
from import_support import ROOT, CSV, fixture_manifest


@pytest.fixture
def catalog(tmp_path, monkeypatch):
    manifest = fixture_manifest(tmp_path)
    sid = json.loads(manifest.read_text())["snapshot_id"]
    load_catalog(CSV,manifest,aliases_path=ROOT/"data/aliases.csv",activate=True)
    monkeypatch.setenv("APP_ENV","ci")
    monkeypatch.setenv("CATALOG_SNAPSHOT_ID",sid)
    sha = os.environ["SOURCE_SHA"]
    monkeypatch.setenv("SOURCE_SHA",sha)
    monkeypatch.setenv("RELEASE_ID","local-"+sha[:12])
    with TestClient(app) as client:
        yield client,sid


def test_every_catalog_endpoint_sql_and_gzip_agree(catalog):
    client,sid = catalog
    prefix = f"/v1/snapshots/{sid}"
    assert client.get("/health/live").json() == {"status":"live"}
    assert client.get("/health/ready").status_code == 200
    assert client.get("/v1/meta").json()["active_snapshot"] == sid
    assert client.get("/v1/snapshots/active").json() == client.get(prefix).json()
    metadata = client.get(prefix).json()
    assert metadata["counts"]["total"] == 5
    profile = client.get(prefix+"/stars/5853498713190525696").json()
    assert profile["source_id"] == "5853498713190525696" and profile["aliases"] == ["Proxima Centauri"]
    assert client.get(prefix+f"/ordinals/{profile['ordinal']}").json() == profile
    sun = client.get(prefix+"/stars/sun").json()
    assert sun["position_pc"] == [0,0,0] and sun["g_magnitude"] is None and sun["ordinal"] == 0
    assert client.get(prefix+"/ordinals/0").json() == sun
    null = client.get(prefix+"/stars/9007199254740993").json()
    assert null["g_magnitude"] is None and null["color_index"] is None
    positions = client.post(prefix+"/positions",json={"ids":["sun",profile["source_id"]]}).json()
    assert positions["snapshot_id"] == sid and positions["items"][1]["position_pc"] == profile["position_pc"]
    response = client.get(prefix+"/map",params={"radius_ly":326.16})
    assert response.status_code == 200,response.text
    manifest = response.json()
    assert manifest["total_count"] == 5
    descriptor = manifest["chunks"][0]
    url = descriptor["url"].removeprefix("/api/catalog")
    downloaded = client.get(url)
    assert downloaded.headers["content-encoding"] == "gzip"
    assert downloaded.headers["cache-control"] == "public, max-age=31536000, immutable"
    # The HTTP client decodes Content-Encoding automatically, exactly like browser fetch.
    assert len(downloaded.content) == descriptor["uncompressed_bytes"]
    assert hashlib.sha256(downloaded.content).hexdigest() == descriptor["uncompressed_sha256"]
    assert downloaded.headers["etag"] == '"'+descriptor["compressed_sha256"]+'"'
    for etag in (downloaded.headers["etag"],"W/"+downloaded.headers["etag"],"*"):
        conditional = client.get(url,headers={"If-None-Match":etag})
        assert conditional.status_code == 304 and conditional.content == b""
    listed = client.get(prefix+"/stars",params={"radius_ly":326.16}).json()["items"]
    assert [r.ordinal for r in decode(downloaded.content)] == [r["ordinal"] for r in listed]
    engine = create_engine(os.environ["CATALOG_READER_DSN"],hide_parameters=True)
    with engine.connect() as c:
        sql_ids = list(c.execute(text("SELECT source_id FROM catalog.stars WHERE snapshot_id=:s ORDER BY distance_pc,source_id"),{"s":sid}).scalars())
    assert [r["source_id"] for r in listed] == sql_ids
    engine.dispose()


def test_search_ranking_pagination_and_cursor_validation(catalog):
    client,sid = catalog
    url = f"/v1/snapshots/{sid}/stars"
    for query in ("Prox","pRoXiMa Centauri","5853498713190525696","585349"):
        result = client.get(url,params={"q":query,"radius_ly":326.16}).json()
        assert result["items"][0]["source_id"] == "5853498713190525696"
    for query in ("%","_","' OR true --","☀"*100):
        response = client.get(url,params={"q":query,"radius_ly":326.16})
        assert response.status_code == 200 and response.json()["items"] == []
    expected = client.get(url,params={"radius_ly":326.16}).json()["items"]
    items,cursor = [],None
    while True:
        params = {"radius_ly":326.16,"limit":2}
        if cursor:
            params["cursor"] = cursor
        response = client.get(url,params=params)
        assert response.status_code == 200,response.text
        page = response.json()
        items.extend(page["items"])
        cursor = page["next_cursor"]
        if not cursor:
            break
        assert len(cursor)<=512
        assert client.get(url,params={**params,"cursor":cursor,"q":"changed"}).status_code == 400
    assert items == expected
    first = client.get(url,params={"limit":2}).json()
    assert client.get(url,params={"radius_ly":"25.0","limit":2,"cursor":first["next_cursor"]}).status_code == 200
    for raw in (b"not json",b"null",b'{}',b'{"after":[0,"NaN","1"]}'):
        token = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        assert client.get(url,params={"cursor":token}).status_code == 400
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _:client.get(url,params={"radius_ly":326.16}).json(),range(10)))
    assert all(result["items"] == expected for result in results)


def test_neighbors_are_separations_and_old_snapshots_survive_switch(catalog,tmp_path):
    client,sid = catalog
    prefix = f"/v1/snapshots/{sid}"
    origin = client.get(prefix+"/stars/5853498713190525696").json()
    neighbors = client.get(prefix+"/stars/5853498713190525696/neighbors",params={"radius_ly":326.16}).json()
    assert len(neighbors["items"]) == 4
    for item in neighbors["items"]:
        assert item["separation_ly"] == pytest.approx(math.dist(origin["position_pc"],item["star"]["position_pc"])*3.261563777)
        assert item["distance_from_sun_ly"] == item["star"]["distance_ly"]
    before = client.get(prefix+"/chunks/000000.bin")
    newer = fixture_manifest(tmp_path)
    load_catalog(CSV,newer,activate=True)
    assert client.get("/v1/snapshots/active").json()["snapshot_id"] != sid
    assert client.get(prefix+"/stars/5853498713190525696").json() == origin
    assert client.get(prefix+"/chunks/000000.bin").content == before.content


def test_catalog_errors_metrics_and_request_ids(catalog):
    client,sid = catalog
    for suffix in ("/stars/999999","/ordinals/999999","/chunks/999999.bin"):
        response = client.get(f"/v1/snapshots/{sid}"+suffix,headers={"X-Request-ID":"catalog-request-1"})
        assert response.status_code == 404
        assert response.json()["error"]["request_id"] == "catalog-request-1"
    assert client.get("/v1/snapshots/unknown").status_code == 404
    assert client.get(f"/v1/snapshots/{sid}/stars",params={"radius_ly":"Infinity"}).status_code == 400
    assert client.get(f"/v1/snapshots/{sid}/stars",params={"limit":101}).status_code == 400
    assert client.post(f"/v1/snapshots/{sid}/positions",json={"ids":[]}).status_code == 422
    assert client.post(f"/v1/snapshots/{sid}/positions",json={"ids":["999999"]}).status_code == 404
    metrics = client.get("/metrics").text
    assert "stellar_http_duration_seconds" in metrics and "stellar_database_pool_checked_out" in metrics
    from prometheus_client.parser import text_string_to_metric_families
    labels = [value for family in text_string_to_metric_families(metrics) for sample in family.samples for value in sample.labels.values()]
    assert "5853498713190525696" not in labels and "999999" not in labels
    assert "local-" not in metrics  # identity labels use the real source SHA and immutable snapshot.
    engine = app.state.engine
    app.state.engine = create_engine("postgresql+psycopg://catalog_reader:invalid@127.0.0.1:1/stellar_catalog",hide_parameters=True,connect_args={"connect_timeout":1})
    try:
        response = client.get("/v1/snapshots/active")
        assert response.status_code == 503 and "invalid@" not in response.text
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 503
    finally:
        app.state.engine.dispose()
        app.state.engine = engine


def test_demo_never_serves_retained_ci_fixtures(catalog):
    from dataclasses import replace
    client,sid = catalog
    settings = app.state.settings
    app.state.settings = replace(settings,app_env="demo")
    try:
        assert client.get("/health/ready").status_code==503
        assert client.get("/v1/snapshots/active").status_code==409
        assert client.get(f"/v1/snapshots/{sid}/stars").status_code==409
        assert client.get(f"/v1/snapshots/{sid}/chunks/000000.bin").status_code==409
    finally:
        app.state.settings = settings
