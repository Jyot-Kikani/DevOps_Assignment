import copy
import hashlib
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from stellar_catalog.app import app as catalog
from stellar_journey.app import app as journey
from stellar_journey.models import EstimateRequest
from schema_models import Release, PhaseReport

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = "gcns-edr3-20261013-20271720"
BODY = {"snapshot_id": SNAPSHOT, "origin_id": "sun", "destination_id": "5853498713190525696", "speed_fraction_c": 0.1}


def test_all_routes_and_internal_boundary():
    cat = TestClient(catalog)
    for url in ["/v1/meta", "/health/ready", "/metrics", "/v1/snapshots/active", f"/v1/snapshots/{SNAPSHOT}",
                f"/v1/snapshots/{SNAPSHOT}/stars", f"/v1/snapshots/{SNAPSHOT}/stars/sun",
                f"/v1/snapshots/{SNAPSHOT}/ordinals/1", f"/v1/snapshots/{SNAPSHOT}/stars/sun/neighbors",
                f"/v1/snapshots/{SNAPSHOT}/map", f"/v1/snapshots/{SNAPSHOT}/chunks/000000.bin"]:
        response = cat.get(url, headers={"X-Request-ID": "contract-test"})
        assert response.status_code == 503, (url, response.text)
        assert response.json()["error"]["request_id"] == "contract-test"
        assert response.headers["X-Request-ID"] == "contract-test"
    assert cat.get("/health/live").json() == {"status": "live"}
    assert cat.post(f"/v1/snapshots/{SNAPSHOT}/positions", json={"ids": ["sun"]}).status_code == 503
    schema = catalog.openapi()
    assert schema["paths"][f"/v1/snapshots/{{snapshot}}/positions"]["post"]["x-internal"] is True
    assert len(schema["paths"]) == 13
    cli = TestClient(journey)
    assert cli.post("/v1/estimate", json=BODY).status_code == 503
    assert cli.post("/v1/journeys", json=BODY, headers={"Idempotency-Key": "00000000-0000-4000-8000-000000000001"}).status_code == 503
    assert cli.get("/v1/journeys/00000000-0000-4000-8000-000000000001").status_code == 503


@pytest.mark.parametrize("change", [{"origin_id": "5853498713190525696"}, {"destination_id": 5853498713190525696},
    {"speed_fraction_c": True}, {"speed_fraction_c": "0.1"}, {"speed_fraction_c": float("nan")},
    {"speed_fraction_c": float("inf")}, {"speed_fraction_c": 0.5001}, {"unexpected": "forbidden"}])
def test_body_rejection(change):
    with pytest.raises(ValidationError):
        EstimateRequest.model_validate(BODY | change)


def test_http_validation_no_reflection_and_bounds():
    client = TestClient(journey)
    assert client.post("/v1/estimate", json=BODY | {"destination_id": 123}).status_code == 422
    response = client.post("/v1/estimate", content='{"bad":', headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert client.post("/v1/estimate", content="x" * 4097).status_code == 400
    assert client.post("/v1/journeys", json=BODY).status_code == 400
    response = client.post("/v1/estimate", json=BODY | {"secret": "fixture-do-not-echo"}, headers={"X-Request-ID": "x" * 65})
    assert "fixture-do-not-echo" not in response.text
    assert len(response.headers["X-Request-ID"]) <= 64
    cat = TestClient(catalog)
    for query in ("limit=0", "limit=101", "radius_ly=NaN", "radius_ly=326.17", "q=" + "x" * 101, "cursor=../"):
        assert cat.get(f"/v1/snapshots/{SNAPSHOT}/stars?{query}").status_code == 400


def release_fixture():
    return {"schema_version": 1, "release_id": "r1-a1-" + "a" * 12, "source_sha": "a" * 40,
        "source_repository": "fixture-owner/DevOps_Assignment", "created_at": "2026-10-19T00:00:00Z",
        "dataset": {"snapshot_id": SNAPSHOT, "raw_sha256": "b" * 64, "fixture": False},
        "images": {role: {"ref": f"ghcr.io/fixture-owner/stellar-atlas-{role}@sha256:" + "c" * 64, "sbom_sha256": "d" * 64}
                   for role in ("web", "catalog", "journey", "importer")},
        "signer_identity": "https://github.com/fixture-owner/DevOps_Assignment/.github/workflows/release.yml@refs/heads/main",
        "compatibility": {"catalog_schema": 1, "journey_schema": 1, "model": "constant-speed-v1"},
        "verification": {"state": "pending"}}


def test_release_schema_rejects_mutable_or_inconsistent_artifacts():
    valid = release_fixture()
    Release.model_validate(valid)
    for mutate in (lambda r: r["images"]["web"].update(ref="ghcr.io/fixture-owner/stellar-atlas-web:latest"),
                   lambda r: r.update(source_sha="b" * 40), lambda r: r["dataset"].update(fixture=True),
                   lambda r: r.update(signer_identity="https://example.com")):
        invalid = copy.deepcopy(valid)
        mutate(invalid)
        with pytest.raises(ValidationError):
            Release.model_validate(invalid)
    PhaseReport.model_validate({"phase": "P02", "status": "in_progress", "checked_at_utc": "2026-10-19T00:00:00Z",
        "source_commit": None, "depends_on": ["P01"], "steps": [], "commands": [], "notes": [], "human_actions": []})


def test_fixture_manifest_hashes_are_independent_of_full_baseline():
    manifest = json.loads((ROOT / "tests/fixtures/catalog/manifest.json").read_text())
    data = ROOT / "tests/fixtures/catalog/catalog.csv"
    assert hashlib.sha256(data.read_bytes()).hexdigest() == manifest["sha256"]
    assert len(data.read_text().splitlines()) - 1 == manifest["rows"] == 5
    assert len(manifest["real_source_ids"]) == 3
    assert len(manifest["synthetic_source_ids"]) == 2
    assert manifest["fixture"] is True
