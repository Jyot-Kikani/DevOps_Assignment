"""P08 loopback development APIs. Stop the named container after the UI check."""
import json
import subprocess
from stellar_ops.bootstrap import ROOT

lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text())
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
subprocess.run(["docker", "run", "-d", "--rm", "--name", "stellar-atlas-web-probe", "--network", "stellar-atlas-db_default",
    "--label", "org.stellar-atlas.scope=maintenance", "-p", "127.0.0.1:18000:18000", "-p", "127.0.0.1:18001:18001",
    "-e", f"SOURCE_SHA={sha}", "-e", f"RELEASE_ID=local-{sha[:12]}",
    "--mount", f"type=bind,source={ROOT},target=/workspace", "--mount", "type=volume,source=stellar-atlas-db-check-env,target=/opt/stellar",
    "-w", "/workspace", "--memory", "512m", lock["images"]["python:3.13-slim-bookworm"]["ref"],
    "python", "tools/db_worker.py", "web-probe"], check=True)
