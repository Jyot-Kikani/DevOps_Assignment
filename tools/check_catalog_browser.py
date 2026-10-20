"""Local P06 browser wire check; no frontend implementation or public routing."""
import json
import argparse
import subprocess
import time
import urllib.request
from uuid import uuid4
from stellar_ops.bootstrap import ROOT, LOCAL
from stellar_ops.quality import node_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-browser",action="store_true",help="Restore the pinned Playwright Chromium into ignored .local/playwright")
    options = parser.parse_args()
    node,env = node_environment()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(LOCAL/"playwright")
    if options.install_browser:
        installed = subprocess.run([node,"apps/web/node_modules/playwright/cli.js","install","chromium"],cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=300)
        (LOCAL/"reports/p06-browser-install.log").write_text(installed.stdout+installed.stderr,encoding="utf-8")
        if installed.returncode:
            raise ValueError("Pinned browser installation failed; see .local/reports/p06-browser-install.log")
    lock = json.loads((ROOT/"tools/toolchain.lock.json").read_text())
    sha = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    name = "stellar-atlas-catalog-probe-"+uuid4().hex[:8]
    args = ["docker","run","--detach","--rm","--name",name,"--label","org.stellar-atlas.scope=maintenance",
        "--network","stellar-atlas-db_default","--publish","127.0.0.1::18000",
        "--env","SOURCE_SHA="+sha,"--env","RELEASE_ID=local-"+sha[:12],
        "--mount",f"type=bind,source={ROOT},target=/workspace",
        "--mount","type=volume,source=stellar-atlas-db-check-env,target=/opt/stellar",
        "--workdir","/workspace","--memory","512m",lock["images"]["python:3.13-slim-bookworm"]["ref"],
        "python","tools/db_worker.py","catalog-probe"]
    subprocess.run(args,check=True,capture_output=True,timeout=120)
    try:
        address = subprocess.check_output(["docker","port",name,"18000"],text=True,timeout=10).strip()
        if not address.startswith("127.0.0.1:"):
            raise ValueError("Diagnostic listener must be loopback only")
        base = "http://"+address
        deadline = time.monotonic()+60
        while time.monotonic()<deadline:
            try:
                with urllib.request.urlopen(base+"/health/ready",timeout=1) as response:
                    if response.status==200:
                        break
            except OSError:
                pass
            time.sleep(0.2)
        else:
            raise ValueError("Catalog diagnostic server did not become ready")
        result = subprocess.run([node,"tools/check_catalog_browser.mjs",base],cwd=ROOT,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=60)
        if result.returncode:
            raise ValueError(result.stderr[-3000:])
        report = json.loads(result.stdout)
        (LOCAL/"reports/p06-browser.json").write_text(json.dumps(report,indent=2))
        print(json.dumps(report,indent=2))
    finally:
        log = subprocess.run(["docker","logs",name],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=15)
        (LOCAL/"reports/p06-browser-server.log").write_text(log.stdout+log.stderr)
        subprocess.run(["docker","stop","--timeout","5",name],capture_output=True,timeout=15)


if __name__ == "__main__":
    main()
