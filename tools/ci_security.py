"""Early CI: publication exclusions, action pins and full-history Gitleaks.

This is not the complete P10/P15 security suite. No cache/artifact upload or login.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import urllib.request

from stellar_ops.bootstrap import ROOT, LOCAL, command, digest, find_tool, write_json
from stellar_ops.guards import local_target
from stellar_ops.locks import verify_locks


def excluded(path):
    parts = PurePosixPath(path).parts
    name = parts[-1]
    if any(part in {".local", "node_modules", ".venv", "venv", ".aws", ".terraform", "screenshots", "traces", "playwright-report", "test-results"} for part in parts):
        return True
    if name.startswith(".env") and name != ".env.example":
        return True
    if ".tfstate" in name or name.endswith((".tfplan", ".dump", ".sqlite", ".sqlite3", ".db", ".gz", ".zip")):
        return True
    if name.endswith(".tfvars"):
        return True
    if name.endswith((".csv", ".bin")):
        return not (path == "data/aliases.csv" or path.startswith("tests/fixtures/"))
    return False


def publication_boundaries():
    objects = subprocess.run(["git", "rev-list", "--objects", "--all"], cwd=ROOT, capture_output=True, check=True, timeout=30).stdout
    checked = subprocess.run(["git", "cat-file", "--batch-check=%(objecttype) %(objectsize) %(rest)"],
                             cwd=ROOT, input=objects, capture_output=True, check=True, timeout=30).stdout.decode("utf-8")
    paths = set()
    violations = set()
    for line in checked.splitlines():
        parts = line.split(" ", 2)
        if len(parts) != 3 or parts[0] != "blob":
            continue
        _, size, path = parts
        paths.add(path)
        if excluded(path) or (path.startswith("tests/fixtures/") and path.endswith((".csv", ".bin")) and int(size) > 65536):
            violations.add(path)
    # rev-list deduplicates blobs, so identical bytes under two historical names
    # can lose a path. Inspect changed names independently, including deleted files.
    historical_names = subprocess.check_output(["git", "log", "--all", "--format=", "--name-only", "--no-renames"],
                                               cwd=ROOT, text=True, timeout=30).splitlines()
    # Include newly staged/uncommitted tracked files during the local pre-push check.
    tracked_names = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True, timeout=30).splitlines()
    for path in historical_names + tracked_names:
        if not path:
            continue
        paths.add(path)
        if excluded(path):
            violations.add(path)
    return {"status": "failed" if violations else "passed", "historical_paths_checked": len(paths), "violations": sorted(violations)}


def action_pins():
    lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text())
    approved = {v["ref"] for v in lock["actions"].values()}
    violations, refs = [], []
    for path in sorted((ROOT / ".github/workflows").glob("*.y*ml")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if not re.match(r"^\s*-?\s*uses:", line):
                continue
            ref = line.split("uses:", 1)[1].split("#", 1)[0].strip()
            refs.append(ref)
            if ref not in approved:
                violations.append(f"{path.name}:{number}: action must match committed SHA lock")
    if not refs:
        violations.append("No workflow action references found")
    return {"status": "failed" if violations else "passed", "references": refs, "violations": violations}


def gitleaks():
    lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text())
    if os.name == "nt":
        executable = find_tool("gitleaks")
        if not executable:
            raise ValueError("Restore pinned Windows Gitleaks using tools-lock")
    else:
        entry = lock["tools_linux"]["gitleaks"]
        target = local_target(LOCAL / "tools/ci-gitleaks")
        target.mkdir(parents=True, exist_ok=True)
        archive = target / "gitleaks.tar.gz"
        with urllib.request.urlopen(entry["url"], timeout=60) as source, archive.open("wb") as output:
            while block := source.read(1024 * 1024):
                output.write(block)
        if digest(archive) != entry["sha256"]:
            raise ValueError("Linux Gitleaks archive checksum mismatch")
        # Extract exactly the executable, never archive-supplied filesystem paths.
        executable = target / "gitleaks"
        with tarfile.open(archive, "r:gz") as bundle:
            member = bundle.getmember("gitleaks")
            if not member.isfile():
                raise ValueError("Gitleaks archive member must be a regular file")
            with bundle.extractfile(member) as source, executable.open("wb") as output:
                output.write(source.read())
        executable.chmod(0o755)
    version = command([str(executable), "version"])
    if version["exit_code"] != 0 or version["stdout"].lstrip("v") != lock["tools"]["gitleaks"]["version"]:
        raise ValueError("Gitleaks version differs from frozen lock")
    return command([str(executable), "git", "--log-opts=--all", "--redact", "--no-banner", "--exit-code", "1",
                    "--report-format", "json", "--report-path", str(LOCAL / "reports/early-ci-gitleaks.json")], timeout=180)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    (LOCAL / "reports").mkdir(parents=True, exist_ok=True)
    report = {"status": "failed", "scope": "Early CI secrets, publication exclusions and action pins; remaining P10/P15 gates pending"}
    try:
        report["locks"] = verify_locks()
        report["publication_boundaries"] = publication_boundaries()
        report["action_pins"] = action_pins()
        if any(report[name]["status"] != "passed" for name in ("locks", "publication_boundaries", "action_pins")):
            raise ValueError("Pre-scan publication/pin checks failed")
        report["gitleaks"] = gitleaks()
        report["status"] = "passed" if report["gitleaks"]["exit_code"] == 0 else "failed"
    except Exception as exc:
        report["error"] = str(exc)
    write_json(LOCAL / "reports/early-ci-security.json", report)
    print(json.dumps(report, indent=2) if args.json else f"Early CI security: {report['status']}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
