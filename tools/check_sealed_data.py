"""P03 full-data local gate, including fresh loopback download. Never publishes."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from uuid import uuid4

from stellar_ops.bootstrap import ROOT, LOCAL, digest, write_json
from stellar_ops.data import seal, publish, fetch_extract, ARCHIVE
from stellar_common.units import estimate


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    first = seal()
    lock = json.loads((ROOT / "data/snapshot.lock.json").read_text())
    first_lock = (ROOT / "data/snapshot.lock.json").read_bytes()
    second = seal()
    assert first["archive_sha256"] == second["archive_sha256"]
    assert first_lock == (ROOT / "data/snapshot.lock.json").read_bytes()
    staged = publish()
    assert publish()["assets"] == staged["assets"]
    directory = ROOT / staged["directory"]
    handler = functools.partial(QuietHandler, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        raw = fetch_extract(f"http://127.0.0.1:{server.server_port}/{ARCHIVE}", lock["archive_sha256"], lock["raw_sha256"],
                            LOCAL / "checks" / ("fresh-data-cache-" + uuid4().hex))
        assert raw.stat().st_size == lock["raw_bytes"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    preserved = json.loads((LOCAL / "reports/p00-preserved-assets.json").read_text())
    for name, entry in preserved.items():
        if name.startswith(("validation", "design")):
            assert digest(ROOT / name) == entry["sha256"], name
    nearest = first["validation"]["nearest_five"]
    result = estimate(nearest[0]["position_pc"], nearest[1]["position_pc"], 0.1)
    assert abs(result["distance_ly"] - 6.586761272382793) < 1e-10
    assert abs(result["duration_julian_years"] - 65.86761272382792) < 1e-9
    report = {"status": "passed", "scope": "Local full-data validation and loopback HTTP; no GitHub publication or public tunnel",
              "deterministic_reseals": 2, "archive_sha256": first["archive_sha256"], "archive_bytes": first["archive_bytes"],
              "fresh_cache_raw_sha256": digest(raw), "immutable_staging_reuse": True,
              "original_validation_and_mockup_hashes_preserved": True, "calculation_oracle": result,
              "counts": first["validation"]["counts"], "assets": staged["assets"]}
    write_json(LOCAL / "reports/p03-full-data.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
