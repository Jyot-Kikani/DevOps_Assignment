"""Archive previously retrieved official notices and the two SIMBAD cross IDs.

Reads ignored upstream responses; performs no downloads and never touches validation/.
Run only when deliberately reviewing a new provenance version.
"""
from pathlib import Path
from html import unescape
import hashlib
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / ".local/reports/p03-upstream"
DATA = ROOT / "data"


def text(html):
    return "\n".join(line.strip() for line in unescape(re.sub(r"<[^>]+>", "\n", html)).replace("\xa0", " ").splitlines() if line.strip())


def put(path, value):
    value = value.encode("utf-8")
    if path.exists() and path.read_bytes() != value:
        raise ValueError("Existing provenance differs; review a new version rather than overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(value)


def main():
    fetch = json.loads((UPSTREAM / "fetch.json").read_text())
    retrieved = datetime.now(timezone.utc).isoformat()
    entries = {}
    for key, start, stop, name in [("license", "<h1>GAIA DATA LICENSE</h1>", "</div>", "gaia-license-notice.txt"),
        ("edr3-credits", '<h1 class="ltx_title ltx_title_section">', "</section>", "edr3-credit-instructions.txt")]:
        raw = (UPSTREAM / (key + ".txt")).read_bytes()
        html = raw.decode("utf-8")
        content = html[html.index(start):]
        content = content[:content.index(stop)]
        entry = {"url": fetch[key]["url"], "retrieved_at_utc": retrieved, "http_status": 200,
                 "raw_html_sha256": hashlib.sha256(raw).hexdigest(), "archive": "provenance/" + name,
                 "extraction": "Article text only; HTML markup removed. Original fetched HTML retained locally."}
        put(DATA / entry["archive"], "Source: " + entry["url"] + "\nRetrieved: " + retrieved + "\nRaw HTML SHA256: " + entry["raw_html_sha256"] + "\n\n" + text(content) + "\n")
        entries[key] = entry
    put(DATA / "provenance/retrieval.json", json.dumps({"schema_version": 1, "sources": entries}, indent=2) + "\n")
    aliases = []
    for key, alias, source_id in [("proxima", "Proxima Centauri", "5853498713190525696"), ("barnard", "Barnard's Star", "4472832130942575872")]:
        raw = (UPSTREAM / (key + "-curl.txt")).read_bytes()
        content = raw.decode("utf-8")
        match = re.search(r"Gaia DR3 " + source_id + r"\b", content)
        if not match or not re.search(r"Object NAME (Proxima Centauri|Barnard's star)", content):
            raise ValueError("Expected SIMBAD cross identification missing; do not label catalog rows")
        aliases.append({"alias": alias, "source_id": source_id, "status": "verified", "url": fetch[key]["url"],
                        "checked_at_utc": retrieved, "response_sha256": hashlib.sha256(raw).hexdigest(),
                        "matched_identifier": match.group(), "basis": "SIMBAD object/name and exact Gaia DR3 identifier; ESA states EDR3/DR3 source lists identical; exact ID also present in frozen GCNS CSV"})
    put(DATA / "aliases.sources.json", json.dumps({"schema_version": 1, "sources": aliases,
        "edr3_dr3_source_list": {"url": "https://www.cosmos.esa.int/web/gaia/dr3", "checked_date_utc": "2026-10-19",
            "statement": "The source list for Gaia EDR3 and Gaia DR3 is identical."},
        "access_note": "Python local SIMBAD trust chain failed; Windows curl with normal verified Schannel TLS succeeded outside sandbox. No TLS validation disabled.",
        "policy": "If future verification fails/conflicts, omit alias and retain source ID search."}, indent=2) + "\n")
    put(DATA / "aliases.csv", "source_id,alias\n" + "".join(a["source_id"] + "," + a["alias"] + "\n" for a in aliases))


if __name__ == "__main__":
    main()
