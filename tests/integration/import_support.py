import json
from pathlib import Path
from uuid import uuid4
from stellar_importer.validation import validate

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "tests/fixtures/catalog/catalog.csv"


def fixture_manifest(tmp_path, *, path=CSV, sid=None):
    base = json.loads((ROOT / "data/snapshot.lock.json").read_text())
    checked = validate(path, fixture=True)
    base.update(snapshot_id=sid or "fixture-" + uuid4().hex, fixture=True,
                raw_sha256=checked["raw_sha256"], raw_bytes=checked["raw_bytes"], counts=checked["counts"])
    target = tmp_path / (base["snapshot_id"] + ".json")
    target.write_text(json.dumps(base))
    return target
