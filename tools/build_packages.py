"""Build first-party wheels and install into isolated, already locked environments."""
from pathlib import Path
import argparse
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def python_for(role):
    return ROOT / ".local/venvs" / role / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["common", "catalog", "journey", "importer"], action="append",
                        help="Rebuild changed packages only; omit for a clean/full build")
    args = parser.parse_args()
    wheels = ROOT / ".local/wheels"
    wheels.mkdir(parents=True, exist_ok=True)
    for name, path in [("common", "packages/python"), ("catalog", "services/catalog"),
                       ("journey", "services/journey"), ("importer", "jobs/importer")]:
        if args.only and name not in args.only:
            continue
        subprocess.run([str(python_for("ops")), "-m", "build", "--wheel", "--no-isolation", "--outdir", str(wheels), path], cwd=ROOT, check=True, timeout=120)
        wheel = wheels / f"stellar_{name}-0.1.0-py3-none-any.whl"
        roles = ("catalog", "journey", "importer", "ops") if name == "common" else (name, "ops")
        for role in roles:
            subprocess.run([str(python_for(role)), "-m", "pip", "install", "--no-deps", "--force-reinstall", "--disable-pip-version-check", str(wheel)], cwd=ROOT, check=True, timeout=60)


if __name__ == "__main__":
    main()
