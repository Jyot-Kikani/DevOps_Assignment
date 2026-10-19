"""Frozen tool restoration and source-lock verification."""
import hashlib
import json
import re
from pathlib import Path

from .bootstrap import ROOT, LOCAL, find_tool


def verify_locks():
    path = ROOT / "tools/toolchain.lock.json"
    lock = json.loads(path.read_text(encoding="utf-8"))
    errors = []
    for name, item in lock["lock_artifacts"].items():
        artifact = ROOT / name
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != item["sha256"]:
            errors.append("Locked artifact mismatch: " + name)
    for name, item in lock["tools"].items():
        if not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) or not item["url"].startswith("https://"):
            errors.append("Invalid native tool provenance: " + name)
    for name, item in lock["actions"].items():
        if not re.fullmatch(r"[a-f0-9]{40}", item["sha"]):
            errors.append("Unpinned GitHub Action: " + name)
    for name, item in lock["images"].items():
        if not re.fullmatch(r"sha256:[a-f0-9]{64}", item["digest"]):
            errors.append("Unpinned image: " + name)
    return {"status": "failed" if errors else "passed", "scope": "committed lock integrity; no installation or host-readiness claim",
            "artifacts_checked": len(lock["lock_artifacts"]), "errors": errors}


def restore_tools():
    verified = verify_locks()
    if verified["status"] != "passed":
        return verified
    from p00_lock import artifact
    lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text(encoding="utf-8"))
    restored = []
    for name, item in lock["tools"].items():
        destination = ROOT / item["local_path"]
        matches = list(destination.rglob(name + ".exe")) if destination.exists() else []
        if not matches:
            artifact(name, item["version"], item["url"], item["sha256"], item["provenance"], item["url"].endswith(".zip"))
            restored.append(name)
        elif not item["url"].endswith(".zip") and hashlib.sha256(matches[0].read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Installed executable checksum mismatch: " + name)
    return {"status": "passed", "scope": "restore exact frozen Windows tools; no dependency re-resolution",
            "restored": restored, "lock_validation": verified}
