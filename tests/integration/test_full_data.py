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
