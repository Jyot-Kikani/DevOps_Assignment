"""Real HTTP subprocesses with each service's own role only."""
from contextlib import contextmanager
import os
import socket
import subprocess
import sys
import time
import httpx


@contextmanager
def live_service(service,sid,tmp_path,*,catalog_url=None,calculation_url=None):
    if service == "journey" and catalog_url and not calculation_url:
        with live_service("calculation",sid,tmp_path,catalog_url=catalog_url) as (base,_):
            with live_service("journey",sid,tmp_path,calculation_url=base) as peer:
                yield peer
        return
    with socket.socket() as listener:
        listener.bind(("127.0.0.1",0))
        port = listener.getsockname()[1]
    env = os.environ.copy()
    own = "CATALOG_READER_DSN" if service in ("catalog", "search", "atlas_map", "snapshot") else "JOURNEY_DSN" if service == "journey" else None
    for key in tuple(env):
        if (key.endswith("_DSN") or key.endswith("_DSN_FILE")) and key != own:
            del env[key]
    env.update(CATALOG_SNAPSHOT_ID=sid,APP_ENV="ci")
    if catalog_url:
        env["CATALOG_INTERNAL_URL"] = catalog_url
    if calculation_url:
        env["CALCULATION_INTERNAL_URL"] = calculation_url
    log_path = tmp_path / (service+"-http.log")
    with log_path.open("w") as log:
        process = subprocess.Popen([sys.executable,"-m","uvicorn",f"stellar_{service}.app:app","--host","127.0.0.1","--port",str(port),"--log-level","warning","--no-access-log"],env=env,stdout=log,stderr=log)
        base = f"http://127.0.0.1:{port}"
        try:
            with httpx.Client(timeout=1,trust_env=False) as client:
                deadline = time.monotonic()+15
                while time.monotonic()<deadline and process.poll() is None:
                    try:
                        if client.get(base+"/health/live").status_code==200:
                            break
                    except httpx.TransportError:
                        pass
                    time.sleep(0.05)
                else:
                    raise AssertionError("Service failed to start: "+log_path.read_text()[-3000:])
            yield base,log_path
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
