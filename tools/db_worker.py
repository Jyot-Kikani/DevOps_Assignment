"""Pinned disposable Linux maintenance/test worker, never an application image."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
VENV = Path("/opt/stellar/venv")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["db-bootstrap", "db-check", "catalog-import", "catalog-report", "catalog-probe", "web-probe"])
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--phase", choices=["P04", "P05", "P06", "P07"])
    args = parser.parse_args()
    if not (VENV / "bin/python").exists():
        venv.EnvBuilder(with_pip=True).create(VENV)
    python = str(VENV / "bin/python")
    with (ROOT / ".local/reports/db-worker-install.log").open("w") as log:
        subprocess.run([python, "-m", "pip", "install", "--require-hashes", "--disable-pip-version-check", "--no-input",
                        "--cache-dir", "/opt/stellar/cache", "-r", "tools/requirements-ops.txt"], stdout=log, stderr=log, check=True, timeout=600)
        wheels = [str(ROOT / f".local/wheels/stellar_{role}-0.1.0-py3-none-any.whl") for role in ("common", "catalog", "journey", "importer", "search", "atlas_map", "snapshot", "calculation")]
        subprocess.run([python, "-m", "pip", "install", "--no-deps", "--force-reinstall", *wheels], stdout=log, stderr=log, check=True, timeout=60)
    subprocess.run([python, "tools/db_tasks.py", args.action] + (["--full"] if args.full else []) +
                   (["--phase", args.phase] if args.phase else []), check=True, timeout=600)


if __name__ == "__main__":
    main()
