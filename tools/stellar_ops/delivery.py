"""P16/P17 tunnel and namespace-scoped GitOps for the existing project cluster."""
import json
import os
import re
import subprocess
import time
import urllib.request
from uuid import uuid4

from .bootstrap import ROOT, LOCAL, digest, find_tool, write_json
from .github import REPOSITORY, api, call
from .kubernetes import apply, kubectl, require_cluster, execute, lock

TUNNEL = LOCAL / 'public'


def public_url():
    record = json.loads((TUNNEL / 'state.json').read_text())
    url = record['url']
    if not re.fullmatch(r'https://[a-z0-9-]+\.trycloudflare\.com', url):
        raise ValueError('Invalid saved Quick Tunnel URL')
    return url


def tunnel_process(record):
    """Check executable, command and creation time before stopping/reusing a PID."""
    if os.name != 'nt':
        raise ValueError('Host tunnel lifecycle currently supports the documented Windows host')
    pid = int(record['pid'])
    script = f'$p=Get-CimInstance Win32_Process -Filter "ProcessId = {pid}"; if ($p) {{ $p | Select-Object ProcessId,ExecutablePath,CommandLine,@{{Name="Created";Expression={{$_.CreationDate.ToUniversalTime().ToString("o")}}}} | ConvertTo-Json -Compress }}'
    output = execute(['powershell.exe', '-NoProfile', '-Command', script], timeout=30)
    if not output:
        return False
    current = json.loads(output)
    return (current['ExecutablePath'].lower() == record['executable'].lower()
        and '--url http://127.0.0.1:8080' in current['CommandLine'] and current['Created'] == record['created'])


def public_start():
    require_cluster()
    from .application import http
    if http('/api/catalog/v1/meta')[0] != 200 or http('/api/journey/v1/meta')[0] != 200:
        raise ValueError('Healthy real Kubernetes gateway required')
    TUNNEL.mkdir(parents=True, exist_ok=True)
    state = TUNNEL / 'state.json'
    if state.exists():
        record = json.loads(state.read_text())
        if tunnel_process(record):
            return {'status': 'passed', 'url': public_url(), 'reused': True, 'external_browser': 'requires separate verification'}
    tool = find_tool('cloudflared')
    if digest(__import__('pathlib').Path(tool)) != lock()['tools']['cloudflared']['sha256']:
        raise ValueError('cloudflared checksum differs from lock')
    log = TUNNEL / 'cloudflared.log'
    # Explicit empty config avoids accidentally using account credentials/configuration.
    config = TUNNEL / 'empty.yml'
    config.write_text('{}\n')
    args = [tool, 'tunnel', '--config', str(config), '--no-autoupdate', '--url', 'http://127.0.0.1:8080',
        '--metrics', '127.0.0.1:20241', '--protocol', 'http2']
    with log.open('wb') as output:
        process = subprocess.Popen(args, cwd=ROOT, stdout=output, stderr=output,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    script = f'Get-CimInstance Win32_Process -Filter "ProcessId = {process.pid}" | Select-Object @{{Name="Created";Expression={{$_.CreationDate.ToUniversalTime().ToString("o")}}}} | ConvertTo-Json -Compress'
    created = json.loads(execute(['powershell.exe', '-NoProfile', '-Command', script]))['Created']
    record = {'pid': process.pid, 'created': created, 'executable': tool, 'url': None}
    write_json(state, record)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        matches = re.findall(r'https://[a-z0-9-]+\.trycloudflare\.com', log.read_text(errors='replace'))
        if matches:
            record['url'] = matches[0]
            write_json(state, record)
            return {'status': 'passed', 'url': record['url'], 'external_browser': 'not yet verified',
                'availability': 'temporary; host, Docker, Kubernetes, tunnel and internet required; no uptime guarantee'}
        if process.poll() is not None:
            raise ValueError('Quick Tunnel exited; inspect .local/public/cloudflared.log')
        time.sleep(1)
    raise ValueError('Quick Tunnel URL not assigned within 60s; inspect project log')


def public_stop():
    state = TUNNEL / 'state.json'
    if not state.exists():
        return {'status': 'passed', 'stopped': False}
    record = json.loads(state.read_text())
    if tunnel_process(record):
        execute(['powershell.exe', '-NoProfile', '-Command', f'Stop-Process -Id {int(record["pid"])} -ErrorAction Stop'])
    state.unlink()
    return {'status': 'passed', 'scope': 'only the recorded project Quick Tunnel; URL invalidated'}


def smoke(target='local'):
    from .application import http
    base = public_url() if target == 'public' else 'http://127.0.0.1:8080'
    def request(path, body=None, headers=None):
        return http(path, body, headers, base=base)
    record = json.loads(request('/release.json')[2])
    if record['dataset']['fixture'] or record['source_repository'] != REPOSITORY:
        raise ValueError('Expected canonical real-data release')
    if json.loads(request('/version.json')[2])['source_sha'] != record['source_sha']:
        raise ValueError('Frontend source mismatch')
    for role in ('catalog', 'journey'):
        status, _, body = request(f'/api/{role}/v1/meta')
        meta = json.loads(body)
        if status != 200 or not meta['readiness'] or meta['source_sha'] != record['source_sha'] or meta['release_id'] != record['release_id']:
            raise ValueError('Running API identity/readiness mismatch: ' + role)
    snapshot = json.loads(request('/api/catalog/v1/snapshots/active')[2])
    if snapshot['raw_sha256'] != record['dataset']['raw_sha256']:
        raise ValueError('Running data checksum mismatch')
    body = {'snapshot_id': snapshot['snapshot_id'], 'origin_id': 'sun', 'destination_id': '5853498713190525696', 'speed_fraction_c': .1}
    status, _, raw = request('/api/journey/v1/estimate', body)
    estimate = json.loads(raw)
    if status != 200 or abs(estimate['distance_ly'] - 4.2464) > .001 or abs(estimate['duration_julian_years'] - estimate['distance_ly'] / .1) > 1e-9:
        raise ValueError('Real Proxima calculation failed')
    status, _, raw = request('/api/journey/v1/journeys', body, {'Idempotency-Key': str(uuid4())})
    journey = json.loads(raw)
    if status != 201 or json.loads(request('/api/journey/v1/journeys/' + journey['id'])[2]) != journey:
        raise ValueError('Shared journey round trip failed')
    for path in ('/metrics', '/admin', '/api/catalog/metrics', '/api/journey/docs', '/api/catalog/health/ready'):
        if request(path)[0] != 404:
            raise ValueError('Private route exposed: ' + path)
    return {'status': 'passed', 'target': target, 'url': base, 'release_id': record['release_id'], 'source_sha': record['source_sha'],
        'snapshot_id': snapshot['snapshot_id'], 'journey_url': base + '/journeys?id=' + journey['id'],
        'distance_ly': estimate['distance_ly'], 'private_routes': 5, 'external_browser': 'separate browser evidence required'}


def gitops_bootstrap():
    require_cluster()
    # Validate deploy exists before installing/enabling auto-sync.
    api(f'repos/{REPOSITORY}/git/ref/heads/deploy')
    record = call(['api', f'repos/{REPOSITORY}/contents/release.json?ref=deploy', '--jq', '.content'])
    import base64
    record = json.loads(base64.b64decode(record))
    from .quality import python_ops
    write_json(LOCAL / 'gitops-release.json', record)
    execute([python_ops(), ROOT / 'tools/check_release.py', LOCAL / 'gitops-release.json'])
    from release import anonymous_images, render_release
    anonymous_images(record)
    # Apply idempotent bootstrap/migrations/import before enabling runtime auto-sync.
    from .kubernetes import run_job
    for job in render_release(record, 'jobs.json')['items']:
        run_job(job)
    apply({'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': 'argocd', 'labels': {'app.kubernetes.io/part-of': 'stellar-atlas'}}})
    for name in ('argocd-crds.yaml', 'argocd-appproject-crd.yaml'):
        path = ROOT / 'infra/vendor/argocd' / name
        if digest(path) != lock()['vendor'][name]['sha256']:
            raise ValueError('Argo CRD checksum mismatch')
        kubectl('apply', '--server-side', '-f', str(path))
    rendered = json.loads(execute([python_ops(), ROOT / 'tools/render_argo.py']))
    kubectl('-n', 'argocd', 'apply', '-f', '-', payload=json.dumps(rendered).encode())
    from .kubernetes import secret
    secret('stellar-cluster', 'argocd', {'name': 'stellar-atlas-local', 'server': 'https://kubernetes.default.svc',
        'namespaces': 'stellar-atlas', 'clusterResources': 'false', 'config': '{}'})
    kubectl('-n', 'argocd', 'label', 'secret', 'stellar-cluster', 'argocd.argoproj.io/secret-type=cluster', '--overwrite')
    for name in ('argocd-server', 'argocd-repo-server', 'argocd-redis'):
        kubectl('-n', 'argocd', 'rollout', 'status', 'deployment/' + name, '--timeout=300s')
    kubectl('-n', 'argocd', 'rollout', 'status', 'statefulset/argocd-application-controller', '--timeout=300s')
    apply(json.loads((ROOT / 'infra/argocd/project.json').read_text()))
    apply(json.loads((ROOT / 'infra/argocd/application.json').read_text()))
    return {'status': 'passed', 'scope': 'namespace install; platform and DB preserved; UI ClusterIP only', 'deployment': 'sync pending; run gitops-check'}


def gitops_check():
    require_cluster()
    kubectl('-n', 'argocd', 'annotate', 'application', 'stellar-atlas', 'argocd.argoproj.io/refresh=hard', '--overwrite')
    expected = api(f'repos/{REPOSITORY}/git/ref/heads/deploy')['object']['sha']
    deadline = time.monotonic() + 300
    while time.monotonic() < deadline:
        application = json.loads(kubectl('-n', 'argocd', 'get', 'application', 'stellar-atlas', '-o', 'json'))
        status = application.get('status', {})
        if status.get('sync', {}).get('status') == 'Synced' and status.get('health', {}).get('status') == 'Healthy' and status['sync']['revision'] == expected:
            record = json.loads(__import__('base64').b64decode(call(['api', f'repos/{REPOSITORY}/contents/release.json?ref=deploy', '--jq', '.content'])))
            for role in ('web', 'catalog', 'journey'):
                deployment = json.loads(kubectl('-n', 'stellar-atlas', 'get', 'deployment', role, '-o', 'json'))
                if deployment['spec']['template']['spec']['containers'][0]['image'] != record['images'][role]['ref']:
                    raise ValueError('Running deployment digest differs from deploy: ' + role)
            report = smoke()
            if report['source_sha'] != record['source_sha'] or report['release_id'] != record['release_id']:
                raise ValueError('Running version differs from deploy')
            report.update(sync='Synced', health='Healthy', deploy_revision=expected)
            return report
        time.sleep(3)
    raise ValueError('Argo did not reach Synced/Healthy at current deploy revision; inspect application status')


def action(name, target='local'):
    return {'public-start': public_start, 'public-stop': public_stop, 'gitops-bootstrap': gitops_bootstrap,
        'gitops-check': gitops_check, 'smoke': lambda: smoke(target)}[name]()
