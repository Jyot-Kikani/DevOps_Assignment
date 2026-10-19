"""Generate P00 dependency locks without creating application scaffolding."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

from run import ROOT, LOCAL, find_tool, write_json
from p00_lock import python_package


def execute(args, label, timeout=300, env=None):
    log = LOCAL / "reports" / (label + ".log")
    try:
        with log.open("w", encoding="utf-8") as output:
            result = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                    timeout=timeout, env=env)
        return {"command": args, "exit_code": result.returncode, "log": str(log.relative_to(ROOT))}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": args, "exit_code": None, "error": str(exc)}


def generate(lock):
    results = {}
    folder = ROOT / "tools/locks"
    folder.mkdir(exist_ok=True)
    groups = {
        "catalog": ["fastapi", "SQLAlchemy", "alembic", "psycopg", "uvicorn", "prometheus-client"],
        "journey": ["fastapi", "SQLAlchemy", "alembic", "psycopg", "uvicorn", "prometheus-client", "httpx"],
        "importer": ["SQLAlchemy", "alembic", "psycopg", "httpx"],
        "quality": ["pytest", "ruff", "bandit", "pip-audit"], "checkov": ["checkov"], "ops": ["pip-tools"],
    }
    for name, packages in groups.items():
        lines = [f"{p}{'[binary]' if p == 'psycopg' else ''}=={lock['python'][p]['version']}" for p in packages]
        (folder / (name + ".in")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    web = folder / "web"
    web.mkdir(exist_ok=True)
    dependencies = {p: v["version"] for p, v in lock["npm"].items()}
    runtime = ("react", "react-dom", "three")
    package = {"name": "stellar-atlas-p00-dependency-lock", "version": "0.0.0", "private": True,
               "type": "module", "engines": {"node": "24.22.0"},
               "dependencies": {p: dependencies[p] for p in runtime},
               "devDependencies": {p: v for p, v in dependencies.items() if p not in runtime}}
    write_json(web / "package.json", package)
    node = Path(find_tool("node"))
    env = os.environ.copy()
    env["PATH"] = str(node.parent) + os.pathsep + env.get("PATH", "")
    results["npm"] = execute([str(node.parent / "npm.cmd"), "install", "--package-lock-only",
        "--ignore-scripts", "--engine-strict", "--no-audit", "--no-fund",
        "--registry=https://registry.npmjs.org", "--cache=" + str(LOCAL / "npm-cache"), "--prefix", str(web)],
        "p00-npm-lock-final", env=env)
    tf = folder / "terraform"
    tf.mkdir(exist_ok=True)
    (tf / "providers.tf").write_text('terraform {\n  required_version = "= 1.16.6"\n  required_providers {\n    kubernetes = {\n      source = "hashicorp/kubernetes"\n      version = "~> 3.2"\n    }\n  }\n}\n', encoding="utf-8")
    env["TF_DATA_DIR"] = str(LOCAL / "terraform-provider-cache")
    if not (tf / ".terraform.lock.hcl").exists():
        results["terraform_init"] = execute([find_tool("terraform"), f"-chdir={tf}", "init", "-backend=false", "-input=false", "-no-color"], "p00-terraform-init-final", env=env)
        results["terraform"] = execute([find_tool("terraform"), f"-chdir={tf}", "providers", "lock", "-platform=windows_amd64", "-platform=linux_amd64", "-no-color"], "p00-terraform-lock-final", env=env)
    else:
        results["terraform"] = {"exit_code": 0, "detail": "Existing provider lock retained; original signed Windows/Linux fetch recorded in p00-terraform-lock.log"}
    resolved = [LOCAL / f"reports/p00-{name}-resolved.txt" for name in groups]
    if not all(p.exists() for p in resolved):
        # Preserve the first attempt's diagnostics before the new run.
        previous = LOCAL / "reports/p00-python-locks.json"
        if previous.exists():
            attempt = LOCAL / "reports/p00-python-first-attempt"
            attempt.mkdir(exist_ok=True)
            for path in (LOCAL / "reports").glob("p00-python-*"):
                if path.is_file() and not (attempt / path.name).exists():
                    (attempt / path.name).write_bytes(path.read_bytes())
        ref = lock["images"]["python:3.13-slim-bookworm"]["ref"]
        args = ["docker", "--context", "desktop-linux", "run", "--rm", "--name", "stellar-atlas-p00-locks",
                "--label", "com.stellar-atlas.phase=P00",
                "--mount", f"type=bind,source={folder},target=/locks",
                "--mount", f"type=bind,source={LOCAL / 'reports'},target=/reports",
                "--mount", f"type=bind,source={ROOT / 'tools/p00_python_locks.py'},target=/p00.py,readonly",
                ref, "python", "-u", "/p00.py"]
        results["python_resolve"] = execute(args, "p00-python-resolve-final", timeout=1200)
    else:
        results["python_resolve"] = {"exit_code": 0, "detail": "Retained exact Linux-resolved transitive versions"}
    pins = {}
    for path in resolved:
        if path.exists():
            for line in path.read_text().splitlines():
                match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^ ;]+)(\s*;.*)?", line.strip())
                if match:
                    pins[(match[1], match[2])] = None
    errors = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(python_package, name, version): (name, version) for name, version in pins}
        for future in as_completed(futures):
            key = futures[future]
            try:
                pins[key] = future.result()
            except Exception as exc:
                errors[str(key)] = str(exc)
    for name, path in zip(groups, resolved):
        if not path.exists():
            errors[name] = "Linux dependency resolution has not produced an output"
            continue
        lines = ["# Linux amd64 / Python 3.13; SHA-256s from official PyPI artifact metadata.",
                 "# Install with pip --require-hashes. Generated by python tools/run.py tools-lock."]
        valid = True
        for line in path.read_text().splitlines():
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^ ;]+)(\s*;.*)?", line.strip())
            if not match:
                if line.strip() and not line.lstrip().startswith("#"):
                    errors[name] = "Unexpected non-pinned requirement: " + line
                    valid = False
                continue
            data = pins.get((match[1], match[2]))
            hashes = sorted({f["sha256"] for f in data["artifacts"]}) if data else []
            if not hashes or not all(re.fullmatch("[0-9a-f]{64}", h) for h in hashes):
                valid = False
                continue
            lines.append(line.strip() + " \\")
            lines.extend("    --hash=sha256:" + h + (" \\" if i < len(hashes)-1 else "") for i, h in enumerate(hashes))
        if valid:
            (folder / (name + ".txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    results["hashes"] = {"exit_code": 1 if errors else 0, "errors": errors,
                         "packages": len(pins), "provenance": "official versioned PyPI JSON artifact digests"}
    write_json(LOCAL / "reports/p00-dependency-locks.json", results)
    return results
