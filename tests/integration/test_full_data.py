"""Explicit full-data gate; not collected in the mandatory CI fixture suite."""
import json
import gzip
import hashlib
import os
import resource
from sqlalchemy import create_engine, text
from stellar_importer.pipeline import load_catalog
from import_support import ROOT


def test_full_sealed_baseline():
    result = load_catalog(ROOT / "validation/gcns_required_fields.csv", ROOT / "data/snapshot.lock.json",
        archive=ROOT / ".local/data/sealed/gcns-edr3-20261013-20271720/gcns-required-fields.csv.gz",
        aliases_path=ROOT / "data/aliases.csv", activate=True)
    assert result["counts"]["rows"] == 331312
    assert result["counts"]["within_100pc"] == 300526
    assert result["counts"]["within_50ly"] == 1151
    assert result["counts"]["within_25ly"] == 142
    assert result["chunks"] == 37
    assert result["map_compressed_bytes"] < 12 * 1024 * 1024
    assert result["default_50ly_chunk_bytes"] < 1024 * 1024
    engine = create_engine(os.environ["CATALOG_READER_DSN"], hide_parameters=True)
    with engine.connect() as c:
        counts = c.execute(text("""SELECT count(*),count(*) FILTER(WHERE distance_pc<=100),
            count(*) FILTER(WHERE distance_ly<=50),count(*) FILTER(WHERE distance_ly<=25),
            count(g_magnitude),count(color_index),max(ordinal) FROM catalog.stars WHERE snapshot_id=:s"""),
            {"s": result["snapshot_id"]}).one()
        assert counts == (331312,300526,1151,142,330881,324310,331312)
        chunks = c.execute(text("SELECT * FROM catalog.map_chunks WHERE snapshot_id=:s ORDER BY chunk_id"), {"s": result["snapshot_id"]}).mappings().all()
        assert len(chunks) == 37 and sum(r["count"] for r in chunks) == 300526
        for chunk in chunks:
            assert hashlib.sha256(chunk["gzip"]).hexdigest() == chunk["compressed_sha256"]
            assert hashlib.sha256(gzip.decompress(chunk["gzip"])).hexdigest() == chunk["uncompressed_sha256"]
    engine.dispose()
    result["worker_peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    result["worker_memory_limit_bytes"] = 512 * 1024 * 1024
    assert result["worker_peak_rss_bytes"] < result["worker_memory_limit_bytes"]
    (ROOT / ".local/reports/p05-full-import.json").write_text(json.dumps(result, indent=2))


def test_full_catalog_http_read_timings(tmp_path):
    import httpx
    import statistics
    import time
    from http_support import live_service
    sid = "gcns-edr3-20261013-20271720"
    timings = {}
    with live_service("catalog",sid,tmp_path) as (base,_):
        with httpx.Client(base_url=base,timeout=10,trust_env=False) as client:
            assert client.get("/health/ready").status_code==200
            prefix = "/v1/snapshots/"+sid
            for radius,count in ((25,142),(50,1151),(326.16,300526)):
                manifest = client.get(prefix+"/map",params={"radius_ly":radius}).json()
                assert manifest["total_count"]==count
            paths = {"profile":prefix+"/stars/5853498713190525696","search":prefix+"/stars?q=Proxima&radius_ly=326.16",
                     "neighbors":prefix+"/stars/5853498713190525696/neighbors?radius_ly=326.16","map":prefix+"/map?radius_ly=50"}
            for name,path in paths.items():
                assert client.get(path).status_code==200
                values = []
                for _ in range(20):
                    started = time.perf_counter()
                    response = client.get(path)
                    assert response.status_code==200,response.text
                    values.append((time.perf_counter()-started)*1000)
                timings[name] = {"requests":20,"median_ms":round(statistics.median(values),3),"max_ms":round(max(values),3)}
            manifest = client.get(prefix+"/map?radius_ly=50").json()
            binary = client.get(manifest["chunks"][0]["url"].removeprefix("/api/catalog"))
            assert len(binary.content)==manifest["chunks"][0]["uncompressed_bytes"]
            timings["default_manifest_bytes"] = len(json.dumps(manifest,separators=(",",":")).encode())
            timings["scope"] = "20 sequential warm requests per endpoint over worker loopback HTTP; P22 concurrency/reference-host/public-path performance remains pending"
    (ROOT / ".local/reports/p06-full-http.json").write_text(json.dumps(timings,indent=2))


def test_full_journey_http_oracle_and_frozen_share_survives_restart(tmp_path):
    import httpx
    import pytest
    from uuid import uuid4
    from http_support import live_service
    sid = "gcns-edr3-20261013-20271720"
    with live_service("catalog",sid,tmp_path) as (catalog_base,catalog_log):
        with httpx.Client(base_url=catalog_base,timeout=5,trust_env=False) as catalog:
            nearest = catalog.get(f"/v1/snapshots/{sid}/stars?radius_ly=50&limit=2").json()["items"]
        request = {"snapshot_id":sid,"origin_id":nearest[0]["source_id"],"destination_id":nearest[1]["source_id"],"speed_fraction_c":0.1}
        key = str(uuid4())
        with live_service("journey",sid,tmp_path,catalog_url=catalog_base) as (journey_base,journey_log):
            with httpx.Client(base_url=journey_base,timeout=5,trust_env=False) as client:
                result = client.post("/v1/estimate",json=request,headers={"X-Request-ID":"full-journey-proof"})
                assert result.status_code==200,result.text
                estimate = result.json()
                assert estimate["distance_ly"]==pytest.approx(6.5867612724,abs=1e-8)
                assert estimate["duration_julian_years"]==pytest.approx(65.867612724,abs=1e-7)
                record = client.post("/v1/journeys",json=request,headers={"Idempotency-Key":key})
                assert record.status_code==201,record.text
                frozen = record.json()
                assert client.get("/v1/journeys/"+frozen["id"]).json()==frozen
                assert "full-journey-proof" in catalog_log.read_text() and "full-journey-proof" in journey_log.read_text()
    # Both services stopped. A new Journey process can return the frozen result with Catalog offline.
    with live_service("journey",sid,tmp_path,catalog_url="http://127.0.0.1:1") as (base,_):
        with httpx.Client(base_url=base,timeout=5,trust_env=False) as client:
            assert client.get("/health/ready").status_code==200
            assert client.get("/v1/journeys/"+frozen["id"]).json()==frozen
            retried = client.post("/v1/journeys",json=request,headers={"Idempotency-Key":key})
            assert retried.status_code==200 and retried.json()==frozen
            assert client.post("/v1/estimate",json=request).status_code==503
            assert client.get("/health/live").status_code==200
            assert client.get("/health/ready").status_code==200
    report = {"status":"passed","snapshot_id":sid,"origin_id":request["origin_id"],"destination_id":request["destination_id"],
              "distance_ly":estimate["distance_ly"],"duration_julian_years":estimate["duration_julian_years"],
              "share_round_trip":"passed","restart_and_catalog_offline_read":"passed","request_id_propagation":"passed"}
    (ROOT/".local/reports/p07-full-http.json").write_text(json.dumps(report,indent=2))
