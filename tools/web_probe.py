"""P08 loopback development APIs. Stop the named container after the UI check."""
import json
import argparse
import subprocess
from stellar_ops.bootstrap import ROOT

lock = json.loads((ROOT / "tools/toolchain.lock.json").read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--fixture', action='store_true', help='Load the tiny attributed CI fixture; never use in demo')
options = parser.parse_args()
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
subprocess.run(["docker", "run", "-d", "--rm", "--name", "stellar-atlas-web-probe", "--network", "stellar-atlas-db_default",
    "--label", "org.stellar-atlas.scope=maintenance", "-p", "127.0.0.1:18000:18000", "-p", "127.0.0.1:18001:18001",
    *[item for p in range(18002,18006) for item in ("-p",f"127.0.0.1:{p}:{p}")],
    "-e", f"SOURCE_SHA={sha}", "-e", f"RELEASE_ID=local-{sha[:12]}", "-e", f"STELLAR_WEB_FIXTURE={int(options.fixture)}",
    "--mount", f"type=bind,source={ROOT},target=/workspace", "--mount", "type=volume,source=stellar-atlas-db-check-env,target=/opt/stellar",
    "-w", "/workspace", "--memory", "512m", lock["images"]["python:3.13-slim-bookworm"]["ref"],
    "python", "tools/db_worker.py", "web-probe"], check=True)
