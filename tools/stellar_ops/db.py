"""Database-only operations; no application deployment or public listener."""
import json
import subprocess
import time
from .bootstrap import ROOT, LOCAL


def run(args, timeout=600):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    attempts = LOCAL / "reports/db-attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    (attempts / f"{time.time_ns()}.log").write_text(f"exit_code={result.returncode}\n" + result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        # Commands/outputs contain no secret values. Workers sanitize DB exceptions.
        raise ValueError("Database command failed: " + (result.stdout + result.stderr)[-6000:])
    return result.stdout.strip()


def action(name, full=False, phase=None):
    compose = ["docker", "compose", "-f", str(ROOT / "compose.database.yml"), "--profile", "database"]
    if name == "db-start":
        if not (LOCAL / "secrets/postgres_admin").is_file():
            raise ValueError("Run secrets-init in the normal user session before db-start")
        run(compose + ["up", "-d", "--wait", "--wait-timeout", "90"])
        return {"status": "passed", "scope": "database only; no host port; named volume retained"}
    if name == "db-stop":
        run(compose + ["stop"])
        return {"status": "passed", "scope": "database stopped; volume retained"}
    lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text())
    image = lock["images"]["python:3.13-slim-bookworm"]["ref"]
    report = LOCAL / "reports" / (name + "-worker.log")
    source_sha = run(["git", "rev-parse", "HEAD"], timeout=30)
    args = ["docker", "run", "--rm", "--network", "stellar-atlas-db_default",
            "--label", "org.stellar-atlas.scope=maintenance",
            "--env", "SOURCE_SHA=" + source_sha, "--env", "RELEASE_ID=local-" + source_sha[:12],
            "--mount", f"type=bind,source={ROOT},target=/workspace",
            "--mount", "type=volume,source=stellar-atlas-db-check-env,target=/opt/stellar",
            "--workdir", "/workspace", "--memory", "512m", "--cpus", "1", image,
            "python", "tools/db_worker.py", name]
    if full:
        args.append("--full")
    if phase:
        args += ["--phase", phase]
    output = run(args, timeout=900)
    report.write_text(output + "\n", encoding="utf-8")
    return {"status": "passed", "log": str(report.relative_to(ROOT)), "output": output[-4000:]}
