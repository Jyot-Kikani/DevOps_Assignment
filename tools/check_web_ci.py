"""Two browser flows against real PostgreSQL/HTTP with the tiny attributed fixture."""
import os
import subprocess
import sys
import time
import urllib.request
from stellar_ops.bootstrap import ROOT, LOCAL
from stellar_ops.quality import node_environment

def main():
    node, env = node_environment()
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(LOCAL / 'playwright')
    env['STELLAR_BASE_URL'] = 'http://127.0.0.1:5173'
    logs = LOCAL / 'reports'
    logs.mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        subprocess.run([node, 'apps/web/node_modules/playwright/cli.js', 'install', '--with-deps', 'chromium'], cwd=ROOT, env=env, check=True, timeout=300)
    try:
        subprocess.run([sys.executable, 'tools/web_probe.py', '--fixture'], cwd=ROOT, check=True, timeout=120)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen('http://127.0.0.1:18000/health/ready', timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            time.sleep(.5)
        else:
            raise ValueError('Fixture-backed web probe did not become ready')
        with (logs / 'ci-vite.log').open('w', encoding='utf-8') as log:
            vite = subprocess.Popen([node, str(ROOT / 'apps/web/node_modules/vite/bin/vite.js'), '--host', '127.0.0.1', '--strictPort'], cwd=ROOT / 'apps/web', env=env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    try:
                        with urllib.request.urlopen('http://127.0.0.1:5173', timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        pass
                    time.sleep(.2)
                else:
                    raise ValueError('Vite did not start')
                npm = str(__import__('pathlib').Path(node).parent / ('npm.cmd' if os.name == 'nt' else 'npm'))
                subprocess.run([npm, '--prefix', 'apps/web', 'run', 'test:e2e'], cwd=ROOT, env=env, check=True, timeout=180)
            finally:
                vite.terminate(); vite.wait(timeout=15)
    finally:
        result = subprocess.run(['docker', 'logs', 'stellar-atlas-web-probe'], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=15)
        (logs / 'ci-web-api.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        subprocess.run(['docker', 'stop', '--timeout', '5', 'stellar-atlas-web-probe'], capture_output=True, timeout=20)

if __name__ == '__main__':
    main()
