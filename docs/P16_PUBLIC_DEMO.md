# P16: temporary public demo

With the existing kind app healthy, run from a normal Windows session:

```powershell
python tools/run.py public-start --json
python tools/run.py smoke --target public --json
# Stop only this project's recorded tunnel when finished:
python tools/run.py public-stop --json
```

The pinned, hash-verified cloudflared executable creates an accountless HTTPS
Quick Tunnel to `http://127.0.0.1:8080`. Its config, log and PID/creation-time
record stay under `.local/public/`. Repeated start reuses the recorded process;
stop verifies its identity before terminating it. No other tunnel is touched.
Tunnel metrics bind to loopback. Databases, monitoring and Argo have no public route.

Use the returned URL on a phone over mobile data or an external browser: Explore,
Proxima calculation, create/reopen a share and `/metrics` returning 404. Save the
actual observation separately. A local HTTP smoke/assigned hostname alone is not
external-browser acceptance. Copy new view/journey links after each new tunnel.

The URL is temporary and changes on a new tunnel. Host power, Docker, kind,
cloudflared and internet are all required; there is no uptime guarantee.
This follows [Cloudflare's Quick Tunnel contract](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
