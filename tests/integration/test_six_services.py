"""Real HTTP across all six processes, using the existing tiny PostgreSQL fixture."""
from contextlib import ExitStack
import json
from uuid import uuid4
import httpx
import pytest
from stellar_importer.pipeline import load_catalog
from import_support import ROOT, CSV, fixture_manifest
from http_support import live_service


def test_six_independent_services_and_journey_http_chain(tmp_path, monkeypatch):
    manifest = fixture_manifest(tmp_path)
    sid = json.loads(manifest.read_text())["snapshot_id"]
    load_catalog(CSV, manifest, aliases_path=ROOT / "data/aliases.csv", activate=True)
    with ExitStack() as stack:
        peers = {}
        for role in ("catalog", "search", "atlas_map", "snapshot"):
            peers[role] = stack.enter_context(live_service(role, sid, tmp_path))[0]
        peers["calculation"] = stack.enter_context(live_service(
            "calculation", sid, tmp_path, catalog_url=peers["catalog"]))[0]
        peers["journey"] = stack.enter_context(live_service(
            "journey", sid, tmp_path, calculation_url=peers["calculation"]))[0]
        with httpx.Client(timeout=10, trust_env=False) as client:
            for role, base in peers.items():
                assert client.get(base + "/health/live").status_code == 200
                assert client.get(base + "/health/ready").status_code == 200
                meta = client.get(base + "/v1/meta").json()
                assert meta["service"] == role and meta["readiness"]
                assert "stellar_version_info" in client.get(base + "/metrics").text
            prefix = f"/v1/snapshots/{sid}"
            assert client.get(peers["snapshot"] + "/v1/snapshots/active").json()["snapshot_id"] == sid
            assert client.get(peers["search"] + prefix + "/stars?q=Proxima&radius_ly=326.16").json()["items"]
            assert client.get(peers["catalog"] + prefix + "/stars/sun").json()["position_pc"] == [0, 0, 0]
            assert client.get(peers["catalog"] + prefix + "/stars").status_code == 404
            assert client.get(peers["search"] + prefix + "/stars/sun").status_code == 404
            map_result = client.get(peers["atlas_map"] + prefix + "/map?radius_ly=50")
            assert map_result.status_code == 200
            chunk = map_result.json()["chunks"][0]["url"].removeprefix("/api/catalog")
            binary = client.get(peers["atlas_map"] + chunk)
            assert binary.status_code == 200 and binary.headers["Content-Encoding"] == "gzip"
            assert client.get(peers["atlas_map"] + chunk, headers={"If-None-Match": binary.headers["ETag"]}).status_code == 304
            body = {"snapshot_id": sid, "origin_id": "sun", "destination_id": "5853498713190525696", "speed_fraction_c": 0.1}
            estimate = client.post(peers["calculation"] + "/v1/estimate", json=body).json()
            assert estimate["distance_ly"] == pytest.approx(4.2463769844, abs=1e-8)
            result = client.post(peers["journey"] + "/v1/journeys", json=body,
                headers={"Idempotency-Key": str(uuid4()), "X-Request-ID": "six-service-proof"})
            assert result.status_code == 201, result.text
            journey = result.json()
            assert journey["distance_ly"] == estimate["distance_ly"]
            assert client.get(peers["journey"] + "/v1/journeys/" + journey["id"]).json() == journey
