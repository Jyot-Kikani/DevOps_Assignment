"""Immutable local data sealing/staging and explicit P15 GitHub publication."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone

from .bootstrap import ROOT, LOCAL, EXPECTED_SHA, digest, write_json, find_tool, command
from .guards import local_target

SNAPSHOT_ID = "gcns-edr3-20261013-20271720"
RELEASE = "data-gcns-edr3-20261013"
ARCHIVE = "gcns-required-fields.csv.gz"
SEALED = LOCAL / "data/sealed" / SNAPSHOT_ID


def immutable_bytes(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != value:
            raise ValueError(f"Immutable artifact differs: {path.name}")
        return "reused"
    try:
        with path.open("xb") as target:
            target.write(value)
    except FileExistsError:
        if path.read_bytes() != value:
            raise ValueError(f"Concurrent immutable artifact differs: {path.name}") from None
    return "created"


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def seal():
    # Run parsing in the installed importer environment, not by importing sibling sources.
    source = ROOT / "validation/gcns_required_fields.csv"
    if digest(source) != EXPECTED_SHA:
        raise ValueError("Preserved validation baseline checksum mismatch; source left untouched")
    raw = local_target(LOCAL / "data/raw/gcns-required-fields.csv")
    raw.parent.mkdir(parents=True, exist_ok=True)
    if not raw.exists():
        with source.open("rb") as src, raw.open("xb") as dst:
            shutil.copyfileobj(src, dst)
    if digest(raw) != EXPECTED_SHA:
        raise ValueError("Existing local raw copy differs; refusing overwrite")
    interpreter = LOCAL / "venvs/importer" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    validation = command([str(interpreter), "-m", "stellar_importer", "validate-baseline", str(raw)], timeout=120)
    if validation["exit_code"] != 0:
        raise ValueError("Baseline validator failed: " + validation.get("stderr", ""))
    report = json.loads(validation["stdout"])
    target = local_target(SEALED / ARCHIVE)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Generate anew every invocation, then compare bytes/hashes before reuse.
    with tempfile.TemporaryDirectory(dir=LOCAL, prefix="seal-") as temporary:
        candidate = Path(temporary) / ARCHIVE
        with raw.open("rb") as src, candidate.open("wb") as dst:
            with gzip.GzipFile(filename="", fileobj=dst, mode="wb", compresslevel=9, mtime=0) as gz:
                shutil.copyfileobj(src, gz, length=1024 * 1024)
        archive_sha = digest(candidate)
        if target.exists():
            if digest(target) != archive_sha:
                raise ValueError("Archive changed under immutable snapshot; review a new transform version")
        else:
            with candidate.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst)
    retained = json.loads((ROOT / "validation/catalog_validation.json").read_text())
    notice_names = ["LICENSE-NOTICE.md", "provenance/gaia-license-notice.txt", "provenance/edr3-credit-instructions.txt",
                    "provenance/retrieval.json", "aliases.csv", "aliases.sources.json"]
    notices = {name: {"sha256": digest(ROOT / "data" / name)} for name in notice_names}
    lock = {"schema_version": 1, "snapshot_id": SNAPSHOT_ID, "transform_version": "1", "catalog_schema_version": 1,
            "fixture": False, "release_tag": RELEASE, "archive_name": ARCHIVE,
            "raw_sha256": EXPECTED_SHA, "raw_bytes": raw.stat().st_size,
            "archive_sha256": archive_sha, "archive_bytes": target.stat().st_size,
            "source_url": retained["source_url"], "source_fetched_date_utc": "2026-10-13",
            "source_fetched_at_precision": "date only retained; exact time is not independently known",
            "source_validated_at_utc": retained["checked_at_utc"], "sealed_validation_date_utc": "2026-10-19",
            "epoch": 2016.0, "catalog": "Gaia EDR3 Catalogue of Nearby Stars (GCNS)",
            "papers": ["https://doi.org/10.1051/0004-6361/202039498", "https://doi.org/10.1051/0004-6361/202039657", "https://doi.org/10.1051/0004-6361/201629272"],
            "license": "CC BY-NC 3.0 IGO", "license_url": "https://www.cosmos.esa.int/web/gaia-users/license",
            "header": report["header"], "units": {"coordinates": "Galactic Cartesian pc", "distance_columns": "kpc", "calculation": "float64 pc/ly"},
            "counts": report["counts"], "notices": notices,
            "publication": {"state": "local_only", "url_template": f"https://github.com/<owner>/stellar-atlas/releases/download/{RELEASE}/{ARCHIVE}", "resolved_url": None},
            "changes": ["Select the frozen 12 source columns; archive exact raw CSV bytes with deterministic gzip", "Normalize optional missing photometry to null in validator; source CSV stays unchanged", "Curated aliases verified separately; calculated distances use published Cartesian positions"]}
    # P03 output includes a committed provenance lock; immutable snapshots never auto-update it.
    immutable_bytes(ROOT / "data/snapshot.lock.json", json_bytes(lock))
    immutable_bytes(SEALED / "snapshot.lock.json", json_bytes(lock))
    immutable_bytes(SEALED / "validation-report.json", json_bytes(report))
    immutable_bytes(ROOT / "data/validation-report.json", json_bytes(report))
    for name in notice_names:
        immutable_bytes(SEALED / name, (ROOT / "data" / name).read_bytes())
    return {"status": "passed", "snapshot_id": SNAPSHOT_ID, "archive_sha256": archive_sha,
            "archive_bytes": target.stat().st_size, "validation": report, "publication": "local_only"}


def asset_manifest(directory):
    return {path.relative_to(directory).as_posix(): {"sha256": digest(path), "bytes": path.stat().st_size}
            for path in sorted(Path(directory).rglob("*")) if path.is_file()}


def publish(stage=None, github=False, repository=None):
    lock = json.loads((ROOT / "data/snapshot.lock.json").read_text())
    if digest(SEALED / ARCHIVE) != lock["archive_sha256"]:
        raise ValueError("Sealed archive checksum mismatch; no publication attempted")
    for name in ("snapshot.lock.json", "validation-report.json"):
        if (SEALED / name).read_bytes() != (ROOT / "data" / name).read_bytes():
            raise ValueError("Sealed metadata differs from committed provenance")
    for name, entry in lock["notices"].items():
        if digest(SEALED / name) != entry["sha256"]:
            raise ValueError("Sealed notice checksum mismatch")
    target = local_target(ROOT / Path(stage) if stage else LOCAL / "data/publication" / RELEASE)
    assets = asset_manifest(SEALED)
    # Preflight the complete set before copying; existing extra/changed files are conflicts.
    if target.exists():
        existing = asset_manifest(target)
        if any(name not in assets or assets[name] != entry for name, entry in existing.items()):
            raise ValueError("Existing immutable release asset differs; refusing overwrite")
    for name in assets:
        destination = target / name
        if not destination.exists():
            immutable_bytes(destination, (SEALED / name).read_bytes())
    if not github:
        return {"status": "passed", "mode": "local_staging", "release_tag": RELEASE, "assets": assets,
                "directory": str(target.relative_to(ROOT)), "public_url": None}
    return publish_github(target, assets, repository, lock)


def publish_github(target, assets, repository, lock):
    if not repository or not re.fullmatch(r"[A-Za-z0-9-]+/stellar-atlas", repository):
        raise ValueError("Explicit --repository <owner>/stellar-atlas required")
    gh = find_tool("gh")
    if not gh:
        raise ValueError("Restore pinned gh first")
    # P15 intentionally uses gh's existing human login/environment. Never launch login or MFA.
    def call(args):
        result = command([gh] + args, timeout=120)
        if result["exit_code"] != 0:
            raise ValueError("GitHub operation failed; no assets overwritten: " + result.get("stderr", ""))
        return result["stdout"]
    repo = json.loads(call(["api", f"repos/{repository}"]))
    if repo["private"] or repo["owner"]["type"] != "User":
        raise ValueError("Data publication requires the inspected public personal repository")
    releases = json.loads(call(["api", f"repos/{repository}/releases", "--paginate", "--slurp"]))
    matches = [r for page in releases for r in page if r["tag_name"] == RELEASE]
    if matches:
        release = matches[0]
        if release["draft"] or release["prerelease"]:
            raise ValueError("Existing release is not the expected immutable public release")
    else:
        call(["release", "create", RELEASE, "--repo", repository, "--title", "GCNS EDR3 frozen educational dataset",
              "--notes-file", str(ROOT / "data/LICENSE-NOTICE.md")])
        release = json.loads(call(["api", f"repos/{repository}/releases/tags/{RELEASE}"]))
    # GitHub assets are flat; all notice basenames are unique.
    flat = {Path(name).name: name for name in assets}
    if len(flat) != len(assets):
        raise ValueError("Data asset basenames must be unique for GitHub publication")
    remote_assets = {a["name"]: a for a in release["assets"]}
    if any(name not in flat for name in remote_assets):
        raise ValueError("Unexpected assets in immutable data release")
    # Verify every existing asset before adding missing assets; never --clobber.
    for name, asset in remote_assets.items():
        expected = assets[flat[name]]
        remote_digest = asset.get("digest")
        if remote_digest != "sha256:" + expected["sha256"] or asset["size"] != expected["bytes"]:
            raise ValueError("Existing remote asset differs or digest unavailable; refusing overwrite")
    for name, relative in flat.items():
        if name not in remote_assets:
            call(["release", "upload", RELEASE, str(target / relative), "--repo", repository])
    # Verify the final complete public set after upload, not just command success.
    final = json.loads(call(["api", f"repos/{repository}/releases/tags/{RELEASE}"]))
    observed = {a["name"]: a for a in final["assets"]}
    if set(observed) != set(flat) or any(observed[n].get("digest") != "sha256:" + assets[p]["sha256"] for n, p in flat.items()):
        raise ValueError("Post-upload public asset verification failed")
    resolved = {"snapshot_id": SNAPSHOT_ID, "release_tag": RELEASE, "archive_sha256": lock["archive_sha256"],
                "url": f"https://github.com/{repository}/releases/download/{RELEASE}/{ARCHIVE}"}
    write_json(LOCAL / "data/publication.resolved.json", resolved)
    resolved_lock = dict(lock, publication={"state": "github", "resolved_url": resolved["url"]})
    immutable_bytes(LOCAL / "data/snapshot.resolved.lock.json", json_bytes(resolved_lock))
    return {"status": "passed", "mode": "github", "assets": assets, "resolved": resolved}


def fetch_extract(url, archive_sha256, raw_sha256, destination):
    """Fresh-cache integrity check. Only explicit HTTPS or local test HTTP URLs."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")):
        raise ValueError("Only HTTPS or explicit loopback HTTP test URLs permitted")
    destination = local_target(destination)
    destination.mkdir(parents=True, exist_ok=False)
    archive, raw = destination / ARCHIVE, destination / "catalog.csv"
    with urllib.request.urlopen(url, timeout=30) as source, archive.open("xb") as target:
        shutil.copyfileobj(source, target)
    if digest(archive) != archive_sha256:
        raise ValueError("Downloaded archive checksum mismatch")
    with gzip.open(archive, "rb") as source, raw.open("xb") as target:
        shutil.copyfileobj(source, target)
    if digest(raw) != raw_sha256:
        raise ValueError("Extracted raw checksum mismatch")
    return raw
