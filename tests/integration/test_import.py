from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from stellar_common.map_format import decode
from stellar_importer.pipeline import load_catalog
from import_support import ROOT, CSV, fixture_manifest


def active():
    engine = create_engine(os.environ["CATALOG_READER_DSN"], hide_parameters=True)
    try:
        with engine.connect() as c:
            return c.execute(text("SELECT snapshot_id FROM catalog.active_snapshot")).scalar()
    finally:
        engine.dispose()


def test_fixture_sql_chunks_concurrency_and_rollback(tmp_path):
    manifest = fixture_manifest(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: load_catalog(CSV, manifest, aliases_path=ROOT / "data/aliases.csv", activate=True), range(2)))
    assert sum(r["activated"] for r in results) == 1
    assert sorted(r["reused"] for r in results) == [False, True]
    sid = results[0]["snapshot_id"]
    assert not load_catalog(CSV, manifest, aliases_path=ROOT / "data/aliases.csv", activate=True)["activated"]
    engine = create_engine(os.environ["CATALOG_WRITER_DSN"], hide_parameters=True)
    with engine.connect() as c:
        stored = c.execute(text("SELECT * FROM catalog.stars WHERE snapshot_id=:s ORDER BY ordinal"), {"s": sid}).mappings().all()
        assert len(stored) == 5 and [r["ordinal"] for r in stored] == [1, 2, 3, 4, 5]
        assert [r["source_id"] for r in stored] == [r["source_id"] for r in sorted(stored, key=lambda r:(r["distance_pc"],int(r["source_id"])))]
        chunks = c.execute(text("SELECT * FROM catalog.map_chunks WHERE snapshot_id=:s"), {"s": sid}).mappings().all()
    assert len(chunks) == 1
    chunk = chunks[0]
    assert hashlib.sha256(chunk["gzip"]).hexdigest() == chunk["compressed_sha256"]
    raw = gzip.decompress(chunk["gzip"])
    assert hashlib.sha256(raw).hexdigest() == chunk["uncompressed_sha256"]
    assert len(raw) == len(stored) * 24
    for binary, row in zip(decode(raw), stored, strict=True):
        assert binary.ordinal == row["ordinal"]
        assert math.isclose(binary.x_pc, row["x"], rel_tol=1e-6, abs_tol=1e-7)
        assert (binary.g_mag is None) == (row["g_magnitude"] is None)
    for sql in ("UPDATE catalog.snapshots SET total_rows=6 WHERE id=:s", "DELETE FROM catalog.stars WHERE snapshot_id=:s", "UPDATE catalog.map_chunks SET count=1 WHERE snapshot_id=:s"):
        with pytest.raises(DBAPIError):
            with engine.begin() as c:
                c.execute(text(sql), {"s": sid})
    newer = fixture_manifest(tmp_path)
    load_catalog(CSV, newer, activate=True)
    assert active() != sid
    assert not load_catalog(CSV, manifest, aliases_path=ROOT / "data/aliases.csv", activate=False)["activated"]
    assert active() != sid
    assert load_catalog(CSV, manifest, aliases_path=ROOT / "data/aliases.csv", activate=True)["activated"]
    assert active() == sid
    engine.dispose()


@pytest.mark.parametrize("kind", ["checksum", "column", "duplicate", "nan", "units", "percentile", "schema", "archive"])
def test_bad_candidate_keeps_active(tmp_path, kind):
    valid = fixture_manifest(tmp_path)
    load_catalog(CSV, valid, activate=True)
    before = active()
    path = tmp_path / "candidate.csv"
    lines = CSV.read_text().splitlines()
    fields = lines[1].split(",")
    if kind == "column":
        lines[0] = lines[0].replace("source_id", "bad_column")
    elif kind == "duplicate":
        lines.append(lines[1])
    elif kind == "nan":
        fields[3] = "NaN"
    elif kind == "units":
        fields[6] = str(float(fields[6]) * 1000)
    elif kind == "percentile":
        fields[7], fields[8] = fields[8], fields[7]
    if kind in ("nan", "units", "percentile"):
        lines[1] = ",".join(fields)
    path.write_text("\n".join(lines) + "\n")
    manifest = json.loads(valid.read_text())
    manifest["snapshot_id"] = "invalid-" + kind + "-" + before[-8:]
    if kind == "checksum":
        manifest["raw_sha256"] = "0" * 64
    if kind != "checksum":
        manifest["raw_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest["raw_bytes"] = path.stat().st_size
    if kind == "schema":
        manifest["catalog_schema_version"] = 2
    if kind == "archive":
        manifest["fixture"] = False
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(manifest))
    with pytest.raises((ValueError, KeyError)):
        load_catalog(path, invalid, activate=True)
    assert active() == before


def test_process_termination_rolls_back_staging(tmp_path):
    base = fixture_manifest(tmp_path)
    load_catalog(CSV, base, activate=True)
    before = active()
    candidate = fixture_manifest(tmp_path)
    sid = json.loads(candidate.read_text())["snapshot_id"]
    marker = tmp_path / "staged"
    script = tmp_path / "interrupted.py"
    script.write_text("from pathlib import Path\nimport time\nfrom stellar_importer.pipeline import load_catalog\n"
                      "def staged(c):\n    Path(" + repr(str(marker)) + ").write_text('staged')\n    time.sleep(120)\n"
                      "load_catalog(" + repr(str(CSV)) + "," + repr(str(candidate)) + ",activate=True,after_staging=staged)\n")
    process = subprocess.Popen([sys.executable, str(script)])
    try:
        deadline = time.monotonic() + 20
        while not marker.exists() and time.monotonic() < deadline and process.poll() is None:
            time.sleep(0.05)
        assert marker.exists()
        assert active() == before
        process.kill()
        process.wait(timeout=10)
        engine = create_engine(os.environ["CATALOG_READER_DSN"], hide_parameters=True)
        with engine.connect() as c:
            assert c.execute(text("SELECT count(*) FROM catalog.snapshots WHERE id=:s"), {"s": sid}).scalar() == 0
            assert c.execute(text("SELECT count(*) FROM catalog.stars WHERE snapshot_id=:s"), {"s": sid}).scalar() == 0
        engine.dispose()
        assert active() == before
        assert load_catalog(CSV, candidate, activate=True)["activated"]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)


def test_demo_rejects_fixture(tmp_path, monkeypatch):
    manifest = fixture_manifest(tmp_path)
    monkeypatch.setenv("APP_ENV", "demo")
    with pytest.raises(ValueError):
        load_catalog(CSV, manifest, activate=True)
