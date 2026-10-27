import asyncio
import time
import httpx
import pytest
from fastapi.testclient import TestClient
from stellar_calculation.app import app
from stellar_calculation.runtime import readiness

def body(sid):
    return {"snapshot_id":sid,"origin_id":"sun","destination_id":"5853498713190525696","speed_fraction_c":0.1}

def test_calculation_catalog_retry_timeout_and_contract_failures(monkeypatch):
    sid = "gcns-test"
    client = TestClient(app)
    original = getattr(app.state, "catalog_client", None)
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
        # Catalog failure does not kill the Calculation process or its configured client.
        assert client.get("/health/live").status_code==200
        assert readiness(app)[0] is True
    finally:
        asyncio.run(mocked.aclose())
        app.state.catalog_client = original
