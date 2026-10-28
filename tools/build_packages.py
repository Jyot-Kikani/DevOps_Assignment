"""Build first-party wheels and install into isolated, already locked environments."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def python_for(role):
    return ROOT / ".local/venvs" / role / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["common", "catalog", "journey", "importer", "search", "atlas_map", "snapshot", "calculation"], action="append",
                        help="Rebuild changed packages only; omit for a clean/full build")
    args = parser.parse_args()
    wheels = ROOT / ".local/wheels"
    wheels.mkdir(parents=True, exist_ok=True)
    for name, path in [("common", "packages/python"), ("catalog", "services/catalog"),
                       ("journey", "services/journey"), ("importer", "jobs/importer"),
                       *[(r, "services/" + r) for r in ("search", "atlas_map", "snapshot", "calculation")]]:
        if args.only and name not in args.only:
            continue
        # Fresh build trees prevent deleted source modules surviving in a reused build/lib.
        staging = ROOT / ".local/build-sources"
        staging.mkdir(parents=True, exist_ok=True)
        source = Path(tempfile.mkdtemp(prefix=name + "-", dir=staging)) / "source"
        shutil.copytree(ROOT / path, source, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__"))
        subprocess.run([str(python_for("ops")), "-m", "build", "--wheel", "--no-isolation", "--outdir", str(wheels), str(source)], cwd=ROOT, check=True, timeout=120)
        wheel = wheels / f"stellar_{name}-0.1.0-py3-none-any.whl"
        # Extracted APIs reuse the existing dependency environments locally.
        environments = {"common": ("catalog", "journey", "importer", "ops"),
                        "search": ("catalog", "ops"), "atlas_map": ("catalog", "ops"),
                        "snapshot": ("catalog", "ops"), "calculation": ("journey", "ops")}
        roles = environments.get(name, (name, "ops"))
        for role in roles:
            subprocess.run([str(python_for(role)), "-m", "pip", "install", "--no-deps", "--force-reinstall", "--disable-pip-version-check", str(wheel)], cwd=ROOT, check=True, timeout=60)


if __name__ == "__main__":
    main()
