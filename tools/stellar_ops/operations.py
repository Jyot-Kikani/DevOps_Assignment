"""P20/P21 operations on the existing kind node; preserve its container and PVC."""
import hashlib
import json
import time
from urllib.error import URLError

from .bootstrap import LOCAL, write_json
from . import kubernetes as k
from .application import http
from . import delivery

NODE = k.CLUSTER + '-control-plane'
STATE = LOCAL / 'kubernetes/demo-stopped.json'


def node():
    info = json.loads(k.execute(['docker', 'inspect', NODE]))[0]
    labels = info['Config'].get('Labels', {})
    ports = info['HostConfig']['PortBindings']
    expected = k.lock()['images']['kindest/node:v1.35.8']['digest']
    if (info['Name'] != '/' + NODE or labels.get('io.x-k8s.kind.cluster') != k.CLUSTER
            or labels.get('io.x-k8s.kind.role') != 'control-plane'
            or info['Config']['Image'].split('@')[-1] != expected
            or ports.get('30080/tcp') != [{'HostIp': '127.0.0.1', 'HostPort': '8080'}]
            or not ports.get('6443/tcp')
            or any(p['HostIp'] != '127.0.0.1' for p in ports['6443/tcp'])):
        raise ValueError('Unexpected project node identity/image/loopback ports; no container changed')
    return info


def pvc():
    obj = json.loads(k.kubectl('-n', 'stellar-data', 'get', 'pvc/postgres-data', '-o', 'json'))
    if obj['status']['phase'] != 'Bound':
        raise ValueError('Postgres PVC is not Bound')
    return {'uid': obj['metadata']['uid'], 'volume': obj['spec']['volumeName']}


def checkpoint():
    return {'sample': k.sample(), 'pvc': pvc(), 'release_id': k.running_release()['release_id']}


def wait_gateway(saved=None, timeout=90):
    deadline = time.monotonic() + timeout
    path = '/api/journey/v1/journeys/' + saved['sample']['journey_id'] if saved else '/api/journey/v1/meta'
    while time.monotonic() < deadline:
        try:
            status, _, raw = http(path)
        except (OSError, URLError):
            status = 503
        if status == 200:
            value = json.loads(raw)
            if saved and value != saved['sample']['journey_http']:
                raise ValueError('Persisted journey changed after restart')
            if saved or value['readiness']:
                return
        elif status not in (502, 503, 504):
            raise ValueError('Unexpected gateway response: ' + str(status))
        time.sleep(1)
    raise ValueError('Gateway did not recover within the bounded wait')


def verify_checkpoint(saved):
    wait_gateway(saved)
    sample = saved['sample']
    # The id came from our real HTTP response; do not interpolate arbitrary state text.
    from uuid import UUID
    journey_id = str(UUID(sample['journey_id']))
    row = k.sql('stellar_journey', "SELECT row_to_json(j)::text FROM journey.journeys j WHERE id='" + journey_id + "'")
    if (hashlib.sha256(row.encode()).hexdigest() != sample['journey_sha256']
            or int(k.sql('stellar_catalog', 'SELECT count(*) FROM catalog.stars')) != sample['catalog_count']
            or k.sql('stellar_catalog', 'SELECT snapshot_id FROM catalog.active_snapshot') != sample['active_snapshot']
            or pvc() != saved['pvc']):
        raise ValueError('Catalog/journey/PVC identity changed; inspect preserved state and host backups')
    return {'catalog_count': sample['catalog_count'], 'active_snapshot': sample['active_snapshot'],
        'journey_id': journey_id, 'identical_journey_http_and_row': True, 'same_bound_pvc': saved['pvc']}


def demo_stop():
    info = node()
    if not info['State']['Running']:
        delivery.public_stop()
        return {'status': 'passed', 'already_stopped': True, 'node': NODE,
            'checkpoint_available': STATE.exists(), 'scope': 'existing node container/PVC retained'}
    k.require_cluster()
    saved = json.loads(STATE.read_text()) if STATE.exists() else None
    if saved and saved['node_id'] != info['Id']:
        raise ValueError('Saved node identity differs; no node stopped')
    if not saved:
        saved = {'node_id': info['Id'], 'checkpoint': checkpoint(),
            'resume_public': False, 'phase': 'stopping'}
        tunnel = delivery.TUNNEL / 'state.json'
        if tunnel.exists():
            record = json.loads(tunnel.read_text())
            saved['resume_public'] = delivery.tunnel_process(record)
            saved['previous_url'] = delivery.public_url()
        # Persist before either stop so an interrupted command can be resumed safely.
        write_json(STATE, saved)
    delivery.public_stop()
    k.execute(['docker', 'stop', '--time', '60', NODE], timeout=100)
    if node()['State']['Running']:
        raise ValueError('Project node still running')
    saved['phase'] = 'stopped'
    write_json(STATE, saved)
    return {'status': 'passed', 'node': NODE, 'container_removed': False, 'pvc_deleted': False,
        'checkpoint': saved['checkpoint'], 'previous_url': saved.get('previous_url'),
        'scope': 'only recorded tunnel and project node stopped; backups and unrelated containers preserved'}


def demo_start(local_only=False):
    info = node()
    saved = json.loads(STATE.read_text()) if STATE.exists() else None
    if saved and saved['node_id'] != info['Id']:
        raise ValueError('Saved node identity differs; no container started')
    if not info['State']['Running']:
        k.execute(['docker', 'start', NODE])
    deadline = time.monotonic() + 180
    while True:
        try:
            k.kubectl('get', 'nodes', '--request-timeout=5s', timeout=10)
            break
        except (ValueError, OSError):
            if time.monotonic() >= deadline:
                raise
            time.sleep(2)
    k.kubectl('wait', '--for=condition=Ready', 'nodes', '--all', '--timeout=180s')
    k.require_cluster()
    for namespace, roles in [('kube-system', ('coredns',)), ('stellar-data', ('postgres',)),
            ('argocd', ('argocd-redis', 'argocd-repo-server', 'argocd-server')),
            ('stellar-atlas', tuple(x['metadata']['name'] for x in json.loads(
                k.kubectl('-n', 'stellar-atlas', 'get', 'deployments', '-o', 'json'))['items']))]:
        for role in roles:
            k.kubectl('-n', namespace, 'rollout', 'status', 'deployment/' + role, '--timeout=180s')
    k.kubectl('-n', 'argocd', 'rollout', 'status', 'statefulset/argocd-application-controller', '--timeout=180s')
    wait_gateway(saved['checkpoint'] if saved else None)
    persistence = verify_checkpoint(saved['checkpoint']) if saved else {'verified': False, 'reason': 'no prior stop checkpoint'}
    gitops = delivery.gitops_check()
    report = {'status': 'passed', 'node': NODE, 'gitops': gitops, 'persistence': persistence,
        'availability': 'single existing local node; no uptime or HA guarantee'}
    if not local_only and (not saved or saved['resume_public']):
        report['tunnel'] = delivery.public_start()
        # New Quick Tunnel DNS/edge routing can lag process startup briefly.
        deadline = time.monotonic() + 90
        while True:
            try:
                report['public_smoke'] = delivery.smoke('public')
                break
            except (OSError, URLError, ValueError):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(3)
    if saved:
        write_json(LOCAL / 'reports/demo-cycle.json', {**report, 'stop': saved})
        STATE.unlink()  # A later start must not compare against an expired historical journey.
    return report


def pod_replace():
    k.require_cluster()
    saved = checkpoint()
    pods = json.loads(k.kubectl('-n', 'stellar-atlas', 'get', 'pods', '-l', 'app=journey', '-o', 'json'))['items']
    ready = [p for p in pods if not p['metadata'].get('deletionTimestamp') and
        any(c['type'] == 'Ready' and c['status'] == 'True' for c in p['status'].get('conditions', []))]
    if len(ready) != 1:
        raise ValueError('Demonstration requires exactly one ready Journey pod')
    old = ready[0]['metadata']
    started = time.monotonic()
    k.kubectl('-n', 'stellar-atlas', 'delete', 'pod', old['name'], '--wait=true', '--timeout=90s')
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        pods = json.loads(k.kubectl('-n', 'stellar-atlas', 'get', 'pods', '-l', 'app=journey', '-o', 'json'))['items']
        ready = [p for p in pods if p['metadata']['uid'] != old['uid'] and not p['metadata'].get('deletionTimestamp') and
            any(c['type'] == 'Ready' and c['status'] == 'True' for c in p['status'].get('conditions', []))]
        if ready:
            break
        time.sleep(1)
    else:
        raise ValueError('Replacement Journey pod did not become Ready')
    k.kubectl('-n', 'stellar-atlas', 'rollout', 'status', 'deployment/journey', '--timeout=180s')
    persistence = verify_checkpoint(saved)
    return {'status': 'passed', 'deleted_pod': old['name'], 'deleted_uid': old['uid'],
        'replacement_pod': ready[0]['metadata']['name'], 'replacement_uid': ready[0]['metadata']['uid'],
        'recovery_seconds': round(time.monotonic() - started, 3), 'persistence': persistence,
        'scope': 'one stateless pod; same node/PVC; elapsed observation, not an HA guarantee'}
