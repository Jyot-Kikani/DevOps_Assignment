"""Install hashed dependencies into isolated project-local Python environments."""
import json
from pathlib import Path
import subprocess
import sys
import venv

from stellar_ops.bootstrap import ROOT, LOCAL, write_json
from stellar_ops.guards import local_target


def install(name, requirement):
    target = local_target(LOCAL / "venvs" / name)
    venv.EnvBuilder(with_pip=True, clear=False).create(target)
    python = target / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if sys.platform != "win32":
        requirement = requirement.replace("-windows", "")
    args = [str(python), "-m", "pip", "install", "--require-hashes", "--no-input",
            "--disable-pip-version-check", "--index-url", "https://pypi.org/simple",
            "--cache-dir", str(LOCAL / "pip-cache"), "--timeout", "25", "--retries", "1", "-r", str(ROOT / requirement)]
    log = LOCAL / "reports" / f"p01-install-{name}.log"
    with log.open("w") as output:
        process = subprocess.run(args, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT, timeout=600)
    checked = subprocess.run([str(python), "-m", "pip", "check"], capture_output=True, text=True, timeout=30)
    return name, {"status": "passed" if process.returncode == checked.returncode == 0 else "failed",
                  "install_exit_code": process.returncode, "pip_check": checked.stdout.strip(),
                  "requirements": requirement, "log": str(log.relative_to(ROOT))}


def main():
    (LOCAL / "reports").mkdir(parents=True, exist_ok=True)
    targets = [("catalog", "services/catalog/requirements-dev-windows.txt"),
               ("journey", "services/journey/requirements-dev-windows.txt"),
               ("importer", "jobs/catalog-importer/requirements-dev-windows.txt"),
               ("ops", "tools/requirements-ops-windows.txt")]
    # EnvBuilder bootstraps executable copies and ensurepip subprocesses. Running
    # four creators concurrently hit Linux ETXTBSY on a fresh hosted runner.
    # Prefer deterministic sequential setup; dependency versions/hashes stay fixed.
    results = {}
    for name, requirement in targets:
        print(f"Preparing locked environment: {name}", flush=True)
        key, result = install(name, requirement)
        results[key] = result
    report = {"status": "passed" if all(r["status"] == "passed" for r in results.values()) else "failed", "environments": results}
    write_json(LOCAL / "reports/p01-environments.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
