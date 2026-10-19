import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
QUERY = "SELECT TOP 100 source_id,xcoord_50,ycoord_50,zcoord_50,dist_50,dist_16,dist_84,phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag FROM gcns.main ORDER BY dist_50"
urls = {
    "inaf_csv": "https://gucds.inaf.it/GCNS/v2forpublication/GCNS_cat.csv",
    "gavo_tap": "https://dc.g-vo.org/tap/sync?" + urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": QUERY}),
}
results = {}
for name, url in urls.items():
    start = time.perf_counter()
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "StellarAtlas-course-feasibility/1.0", "Range": "bytes=0-32767"} if name == "inaf_csv" else {"User-Agent": "StellarAtlas-course-feasibility/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            content = response.read(32768)
            (ROOT / (name + "_sample.csv")).write_bytes(content)
            results[name] = {"url": url, "status": response.status, "content_type": response.headers.get("Content-Type"), "content_length": response.headers.get("Content-Length"), "content_range": response.headers.get("Content-Range"), "bytes_read": len(content), "seconds": round(time.perf_counter() - start, 2), "first_lines": content.decode("utf-8", "replace").splitlines()[:3]}
    except Exception as exc:
        results[name] = {"url": url, "error": str(exc), "seconds": round(time.perf_counter() - start, 2)}
(ROOT / "source_probe.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
print(json.dumps(results, indent=2))
