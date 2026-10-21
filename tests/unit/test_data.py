import csv
import hashlib
import io
import json
from pathlib import Path
from uuid import uuid4
import pytest
from stellar_importer.validation import HEADER, validate, rows, BASELINE_COUNTS
from stellar_ops import data

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/catalog/catalog.csv"


def test_fixture_validation_and_nulls():
    manifest = json.loads(FIXTURE.with_name("manifest.json").read_text())
    result = validate(FIXTURE, expected_sha256=manifest["sha256"], expected_rows=5, fixture=True)
    assert result["counts"]["rows"] == 5 and result["fixture"]
    assert result["counts"]["valid_brightness"] == 4
    normalized = list(rows(FIXTURE))
    edge = next(r for r in normalized if r["source_id"] == "9007199254740993")
    assert edge["g_magnitude"] is None and edge["color_index"] is None
    with pytest.raises(ValueError, match="counts differ"):
        validate(FIXTURE, expected_counts=BASELINE_COUNTS)
    with pytest.raises(ValueError, match="checksum"):
        validate(FIXTURE, expected_sha256="0" * 64)


@pytest.mark.parametrize("change", ["header", "duplicate", "nan", "distance", "percentiles", "id", "photometry"])
def test_invalid_catalog(tmp_path, change):
    with FIXTURE.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fixture = list(reader)
    fields = list(HEADER)
    if change == "header":
        fields = fields[:-1]
        for row in fixture:
            row.pop("phot_rp_mean_mag")
    elif change == "duplicate":
        fixture.append(dict(fixture[0]))
    else:
        key, value = {"nan": ("xcoord_50", "NaN"), "distance": ("dist_50", "100"),
                      "percentiles": ("dist_16", "1"), "id": ("source_id", "1e19"),
                      "photometry": ("phot_g_mean_mag", "Infinity")}[change]
        fixture[0][key] = value
    target = tmp_path / "invalid.csv"
    with target.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(fixture)
    with pytest.raises(ValueError):
        validate(target)


def test_immutable_publication_preflight(monkeypatch):
    # A tiny isolated release set tests no-overwrite behavior without large baseline copies.
    boundary = ROOT / ".local/checks" / ("publication-" + uuid4().hex)
    sealed, stage = boundary / "sealed", boundary / "stage"
    sealed.mkdir(parents=True)
    metadata = {"archive_sha256": hashlib.sha256(b"fixture archive").hexdigest(), "notices": {}}
    (sealed / data.ARCHIVE).write_bytes(b"fixture archive")
    (sealed / "snapshot.lock.json").write_text(json.dumps(metadata))
    (sealed / "validation-report.json").write_text('{"fixture":true}')
    # publish compares provenance to ROOT/data; isolate ROOT without weakening real containment.
    fake_root = boundary / "root"
    (fake_root / "data").mkdir(parents=True)
    for name in ("snapshot.lock.json", "validation-report.json"):
        (fake_root / "data" / name).write_bytes((sealed / name).read_bytes())
    monkeypatch.setattr(data, "SEALED", sealed)
    monkeypatch.setattr(data, "ROOT", boundary)
    # Root/data files for the immutable committed provenance comparison.
    (boundary / "data").mkdir()
    for name in ("snapshot.lock.json", "validation-report.json"):
        (boundary / "data" / name).write_bytes((sealed / name).read_bytes())
    first = data.publish(stage=stage)
    assert first["status"] == "passed" and first["public_url"] is None
    assert data.publish(stage=stage)["assets"] == first["assets"]
    changed = stage / data.ARCHIVE
    changed.write_bytes(b"changed fixture")
    with pytest.raises(ValueError, match="refusing overwrite"):
        data.publish(stage=stage)
    assert changed.read_bytes() == b"changed fixture"
    with pytest.raises(ValueError, match="child"):
        data.publish(stage=ROOT / "validation")


def test_download_rejects_corrupt_archive(monkeypatch):
    target = ROOT / ".local/checks" / ("corrupt-cache-" + uuid4().hex)
    monkeypatch.setattr(data.urllib.request, "urlopen", lambda *a, **k: io.BytesIO(b"corrupt test bytes"))
    with pytest.raises(ValueError, match="archive checksum"):
        data.fetch_extract("https://example.com/fixture.gz", "0" * 64, "0" * 64, target)
    assert not (target / "catalog.csv").exists()
    with pytest.raises(ValueError, match="Only HTTPS"):
        data.fetch_extract("http://example.com/fixture.gz", "0" * 64, "0" * 64, target)


def test_github_publication_digest_and_rights_fail_safely(monkeypatch):
    """Mock API proves remote decisions; no GitHub request or publication occurs."""
    boundary = ROOT / ".local/checks" / ("github-contract-" + uuid4().hex)
    boundary.mkdir(parents=True)
    (boundary / "fixture.txt").write_bytes(b"fixture bytes")
    asset = {"fixture.txt": {"sha256": hashlib.sha256(b"fixture bytes").hexdigest(), "bytes": 13}}
    metadata = {"archive_sha256": "a" * 64}
    uploads = []
    state = {"private": True, "digest": "sha256:" + asset["fixture.txt"]["sha256"], "present": True}

    def fake_command(args, **kwargs):
        if args[1:3] == ["api", "repos/Jyot-Kikani/DevOps_Assignment"]:
            result = {"private": state["private"], "owner": {"type": "User"}}
        elif args[1] == "api":
            release = {"tag_name": data.RELEASE, "draft": False, "prerelease": False,
                "assets": [{"name": "fixture.txt", "size": 13, "digest": state["digest"]}] if state["present"] else []}
            result = [[release]] if "--paginate" in args else release
        else:
            uploads.append(args)
            state["present"] = True
            result = {}
        return {"exit_code": 0, "stdout": json.dumps(result), "stderr": ""}

    monkeypatch.setattr(data, "find_tool", lambda _: "gh-fixture")
    from stellar_ops import github
    monkeypatch.setattr(github, "call", lambda args: fake_command(["gh-fixture", *args])["stdout"])
    monkeypatch.setattr(data, "LOCAL", boundary)
    with pytest.raises(ValueError, match="public personal"):
        data.publish_github(boundary, asset, "Jyot-Kikani/DevOps_Assignment", metadata)
    state["private"] = False
    state["digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="refusing overwrite"):
        data.publish_github(boundary, asset, "Jyot-Kikani/DevOps_Assignment", metadata)
    assert not uploads
    state["digest"] = "sha256:" + asset["fixture.txt"]["sha256"]
    result = data.publish_github(boundary, asset, "Jyot-Kikani/DevOps_Assignment", metadata)
    assert result["status"] == "passed" and not uploads
    state["present"] = False
    data.publish_github(boundary, asset, "Jyot-Kikani/DevOps_Assignment", metadata)
    assert len(uploads) == 1 and "--clobber" not in uploads[0]
