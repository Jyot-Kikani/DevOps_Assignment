"""P12–P14 local operations. Explicit context; no publication or cluster deletion."""
import base64
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import socket
import subprocess
import time
from urllib.parse import quote
from uuid import uuid4

from .bootstrap import ROOT, LOCAL, find_tool, write_json
from .guards import local_target

CLUSTER = 'stellar-atlas-demo'
CONTEXT = 'kind-' + CLUSTER
WORK = LOCAL / 'kubernetes'
CONFIG = WORK / 'config'


def execute(args, *, payload=None, binary=False, allowed=(0,), timeout=600, private=False):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, input=payload,
        capture_output=True, timeout=timeout)
    if result.returncode not in allowed:
        detail = 'private input/output withheld' if private else (result.stdout + result.stderr).decode('utf-8', errors='replace')[-4000:]
        raise ValueError(f'Local operation failed (exit {result.returncode}): {detail}')
    return result.stdout if binary else result.stdout.decode('utf-8', errors='replace').strip()


def kubectl(*args, **kwargs):
    return execute([find_tool('kubectl'), '--kubeconfig', CONFIG, '--context', CONTEXT, *args], **kwargs)


def apply(document, private=False):
    return kubectl('apply', '-f', '-', payload=json.dumps(document).encode(), private=private)


def lock():
    return json.loads((ROOT / 'tools/toolchain.lock.json').read_text())


def require_cluster():
    config = json.loads(kubectl('config', 'view', '-o', 'json'))
    current = next(x for x in config['contexts'] if x['name'] == CONTEXT)
    cluster = next(x for x in config['clusters'] if x['name'] == current['context']['cluster'])
    if not cluster['cluster']['server'].startswith('https://127.0.0.1:'):
        raise ValueError('Project API must be loopback-only')
    nodes = json.loads(kubectl('get', 'nodes', '-o', 'json'))['items']
    if len(nodes) != 1 or nodes[0]['metadata']['name'] != CLUSTER + '-control-plane':
        raise ValueError('Refusing an unexpected Kubernetes cluster')


def cluster_create():
    WORK.mkdir(parents=True, exist_ok=True)
    kind = find_tool('kind')
    if 'v' + lock()['tools']['kind']['version'] not in execute([kind, 'version']):
        raise ValueError('kind version differs from lock')
    clusters = execute([kind, 'get', 'clusters']).splitlines()
    if CLUSTER not in clusters:
        with socket.socket() as probe:
            try:
                probe.bind(('127.0.0.1', 8080))
            except OSError:
                raise ValueError('Port 8080 is occupied; stop only Stellar Atlas Compose with dev-down, or resolve its owner first') from None
        execute([kind, 'create', 'cluster', '--config', ROOT / 'infra/kind/cluster.yaml', '--kubeconfig', CONFIG, '--wait', '180s'], timeout=900)
    else:
        execute([kind, 'export', 'kubeconfig', '--name', CLUSTER, '--kubeconfig', CONFIG])
    require_cluster()
    from .secrets import restrict
    restrict(CONFIG)
    inspect = json.loads(execute(['docker', 'inspect', CLUSTER + '-control-plane']))[0]
    binding = inspect['HostConfig']['PortBindings'].get('30080/tcp', [])
    if binding != [{'HostIp': '127.0.0.1', 'HostPort': '8080'}] or inspect['Config']['Image'].split('@')[-1] != lock()['images']['kindest/node:v1.35.8']['digest']:
        raise ValueError('Existing project node image/loopback mapping differs from the locked configuration; no automatic deletion')
    kubectl('wait', '--for=condition=Ready', 'nodes', '--all', '--timeout=180s')
    kubectl('-n', 'kube-system', 'rollout', 'status', 'deployment/coredns', '--timeout=120s')
    return {'status': 'passed', 'cluster': CLUSTER, 'networking': 'default kind CNI; loopback API and gateway; local-path storage'}


def platform(root, do_apply=False, monitoring=False):
    require_cluster()
    directory = local_target(LOCAL / 'terraform' / root)
    directory.mkdir(parents=True, exist_ok=True)
    tfdata = directory / 'data'
    env_path = directory / 'settings.json'
    settings = json.loads(env_path.read_text()) if env_path.exists() else {}
    if monitoring:
        settings['monitoring'] = True
        write_json(env_path, settings)
    variables = {'kubeconfig': CONFIG.as_posix()}
    if root == 'runtime':
        variables['monitoring'] = settings.get('monitoring', False)
    write_json(directory / 'inputs.tfvars.json', variables)
    args = [find_tool('terraform'), '-chdir=' + str(ROOT / 'infra/terraform' / root)]
    env = os.environ.copy()
    env.update(TF_DATA_DIR=str(tfdata), TF_IN_AUTOMATION='1')
    def tf(*items, allowed=(0,)):
        result = subprocess.run([*args, *items], cwd=ROOT, env=env, capture_output=True, timeout=600)
        output = (result.stdout + result.stderr).decode('utf-8', errors='replace')
        (directory / (items[0] + '.log')).write_text(output, encoding='utf-8')
        if result.returncode not in allowed:
            raise ValueError('Terraform ' + items[0] + ' failed: ' + output[-4000:])
        return result.returncode
    tf('init', '-input=false', '-lockfile=readonly', '-backend-config=path=' + str(directory / 'terraform.tfstate'))
    tf('validate', '-no-color')
    plan = directory / 'platform.tfplan'
    code = tf('plan', '-input=false', '-no-color', '-detailed-exitcode', '-var-file=' + str(directory / 'inputs.tfvars.json'), '-out=' + str(plan), allowed=(0, 2))
    if do_apply:
        tf('apply', '-input=false', '-no-color', str(plan))
    return {'status': 'passed', 'root': root, 'changes': code == 2, 'applied': do_apply,
        'state': '.local/terraform/' + root, 'monitoring': variables.get('monitoring', False)}


def secret(name, namespace, values):
    # No credentials in command arguments, Terraform, files or returned diagnostics.
    document = {'apiVersion': 'v1', 'kind': 'Secret', 'metadata': {'name': name, 'namespace': namespace},
        'type': 'Opaque', 'data': {k: base64.b64encode(v.encode()).decode() for k, v in values.items()}}
    kubectl('apply', '--server-side', '--field-manager=stellar-secrets', '-f', '-', payload=json.dumps(document).encode(), private=True)


def cluster_secrets():
    require_cluster()
    from .secrets import initialize
    initialize()
    def value(name): return (LOCAL / 'secrets' / name).read_text().strip()
    secret('postgres-admin', 'stellar-data', {'postgres_admin': value('postgres_admin')})
    secret('bootstrap', 'stellar-atlas', {n: value(n) for n in ('postgres_admin', 'catalog_writer', 'catalog_reader', 'journey_owner', 'journey_app')})
    for role, database in [('catalog_writer', 'stellar_catalog'), ('catalog_reader', 'stellar_catalog'), ('journey_owner', 'stellar_journey'), ('journey_app', 'stellar_journey')]:
        dsn = f'postgresql+psycopg://{role}:{quote(value(role), safe="")}@postgres.stellar-data.svc.cluster.local/{database}'
        secret(role.replace('_', '-'), 'stellar-atlas', {role + '_dsn': dsn})
    secret('grafana-admin', 'stellar-monitoring', {'grafana_admin': value('grafana_admin')})
    return {'status': 'passed', 'scope': 'role-specific Kubernetes secrets; values never printed or stored in Terraform'}


def release():
    record = json.loads((LOCAL / 'release.json').read_text())
    if record['source_dirty'] or record['dataset']['fixture']:
        raise ValueError('Kubernetes requires prepared clean-source, real-data images')
    return record


def image_refs(record):
    return {role: 'docker.io/library/stellar-atlas-' + role + '@' + image['manifest_digest'] for role, image in record['images'].items()}


def render(name, record):
    values = {'IMAGE_' + role.upper().replace('-', '_'): ref for role, ref in image_refs(record).items()}
    values.update(RELEASE_ID=record['release_id'], SNAPSHOT_ID=record['dataset']['snapshot_id'])
    def replace(item):
        if isinstance(item, str): return values.get(item, item)
        if isinstance(item, list): return [replace(x) for x in item]
        if isinstance(item, dict): return {k: v if k == 'name' else replace(v) for k, v in item.items()}
        return item
    return replace(json.loads((ROOT / 'deploy/local' / name).read_text()))


def load_images(record):
    for role, image in record['images'].items():
        info = json.loads(execute(['docker', 'image', 'inspect', image['local_tag']]))[0]
        if info['Descriptor']['digest'] != image['manifest_digest'] or info['Config']['Labels']['org.opencontainers.image.revision'] != record['source_sha']:
            raise ValueError('Prepared image identity mismatch: ' + role)
        execute([find_tool('kind'), 'load', 'docker-image', '--name', CLUSTER, image['local_tag']], timeout=900)
        target = image_refs(record)[role]
        execute(['docker', 'exec', CLUSTER + '-control-plane', 'ctr', '-n', 'k8s.io', 'images', 'tag', '--force', 'docker.io/library/' + image['local_tag'], target])
        actual = json.loads(execute(['docker', 'exec', CLUSTER + '-control-plane', 'crictl', 'inspecti', target]))
        if image['manifest_digest'] not in json.dumps(actual['status']['repoDigests']):
            raise ValueError('kind image digest does not match prepared release: ' + role)


def run_job(document):
    name = document['metadata']['name']
    kubectl('-n', 'stellar-atlas', 'delete', 'job', name, '--ignore-not-found=true', '--wait=true')
    apply(document)
    deadline = time.monotonic() + 660
    while time.monotonic() < deadline:
        status = json.loads(kubectl('-n', 'stellar-atlas', 'get', 'job', name, '-o', 'json'))['status']
        if status.get('succeeded'):
            return
        if status.get('failed'):
            raise ValueError('Job failed: ' + name + '; inspect its private pod logs locally')
        time.sleep(2)
    raise ValueError('Job timeout: ' + name)


def demo_bootstrap():
    require_cluster()
    record = release()
    load_images(record)
    kubectl('-n', 'stellar-data', 'rollout', 'status', 'deployment/postgres', '--timeout=180s')
    app = render('app.json', record)
    apply(app['items'][0])  # private DB DNS alias needed by the reused bootstrap job
    for job in render('jobs.json', record)['items']:
        run_job(job)
    apply({'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'release', 'namespace': 'stellar-atlas'}, 'data': {'release.json': json.dumps(record)}})
    apply(app)
    for role in ('catalog', 'search', 'atlas-map', 'snapshot', 'calculation', 'journey', 'web'):
        kubectl('-n', 'stellar-atlas', 'rollout', 'status', 'deployment/' + role, '--timeout=180s')
    from .application import smoke
    report = smoke()
    report['deployment'] = 'local kind; immutable image digests; manual bootstrap; no Argo or publication'
    return report


@contextmanager
def forward(namespace, service, port, local_port=None):
    if local_port is None:
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            local_port = s.getsockname()[1]
    args = [find_tool('kubectl'), '--kubeconfig', str(CONFIG), '--context', CONTEXT, '-n', namespace,
        'port-forward', 'service/' + service, f'{local_port}:{port}', '--address=127.0.0.1']
    process = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise ValueError('Private port-forward exited; check port owner and pod readiness')
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1', local_port)) == 0:
                    break
            time.sleep(.1)
        else:
            raise ValueError('Private port-forward timeout')
        yield local_port
    finally:
        process.terminate()
        process.wait(timeout=15)


def db_exec(*args, payload=None, binary=False, namespace='stellar-data', deployment='postgres'):
    return kubectl('-n', namespace, 'exec', '-i', 'deployment/' + deployment, '--', *args,
        payload=payload, binary=binary, private=True)


def sql(database, statement, namespace='stellar-data', deployment='postgres'):
    return db_exec('psql', '-U', 'postgres', '-d', database, '-At', '-v', 'ON_ERROR_STOP=1', '-c', statement,
        namespace=namespace, deployment=deployment)


def running_release():
    from .application import http
    status, _, raw = http('/release.json')
    record = json.loads(raw)
    if status != 200 or record.get('source_dirty') or record['dataset']['fixture']:
        raise ValueError('A healthy real-data running release is required')
    if json.loads(http('/version.json')[2])['source_sha'] != record['source_sha']:
        raise ValueError('Running web/release identity mismatch')
    return record


def sample():
    from .application import http
    sid = running_release()['dataset']['snapshot_id']
    stars = json.loads(http(f'/api/catalog/v1/snapshots/{sid}/stars?q=Proxima')[2])
    star = stars['items'][0]['source_id']
    if star != '5853498713190525696':
        raise ValueError('Verified Proxima search did not return the expected source')
    status, _, raw = http('/api/journey/v1/journeys', {'snapshot_id': sid, 'origin_id': 'sun', 'destination_id': star, 'speed_fraction_c': .1}, {'Idempotency-Key': str(uuid4())})
    if status != 201:
        raise ValueError('Cannot create recovery sample')
    journey = json.loads(raw)
    if abs(journey['distance_ly'] - 4.24637698440337) > 1e-8:
        raise ValueError('Real Proxima calculation differs from the established oracle')
    # Row representation is stable across pg_dump/restore, unlike HTTP key ordering.
    row = sql('stellar_journey', "SELECT row_to_json(j)::text FROM journey.journeys j WHERE id='" + journey['id'] + "'")
    return {'journey_id': journey['id'], 'journey_sha256': hashlib.sha256(row.encode()).hexdigest(),
        'catalog_count': int(sql('stellar_catalog', 'SELECT count(*) FROM catalog.stars')),
        'active_snapshot': sql('stellar_catalog', 'SELECT snapshot_id FROM catalog.active_snapshot'), 'journey_http': journey}


def backup():
    require_cluster()
    directory = local_target(LOCAL / 'backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    directory.mkdir(parents=True)
    from .secrets import restrict
    restrict(directory, True)
    record = sample()
    record['databases'] = {}
    for database in ('stellar_catalog', 'stellar_journey'):
        raw = db_exec('pg_dump', '-U', 'postgres', '-d', database, '-Fc', binary=True)
        if not raw.startswith(b'PGDMP'):
            raise ValueError('Invalid custom-format database dump')
        path = directory / (database + '.dump')
        path.write_bytes(raw)
        record['databases'][database] = {'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}
    record['release'] = running_release()
    write_json(directory / 'manifest.json', record)
    write_json(WORK / 'latest-backup.json', {'directory': str(directory.relative_to(LOCAL))})
    return {'status': 'passed', 'backup': str(directory.relative_to(ROOT)), 'catalog_count': record['catalog_count'], 'journey_id': record['journey_id'], 'format': 'two host-side pg_dump custom archives; current-user-only directory; originals retained'}


def restore():
    require_cluster()
    pointer = json.loads((WORK / 'latest-backup.json').read_text())
    directory = local_target(LOCAL / pointer['directory'])
    if not directory.is_relative_to((LOCAL / 'backups').resolve()):
        raise ValueError('Restore source must be beneath .local/backups')
    record = json.loads((directory / 'manifest.json').read_text())
    # Unique target with emptyDir; never point a restore at production or its PVC.
    namespace = 'stellar-restore-' + uuid4().hex[:8]
    apply({'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': namespace, 'labels': {'app.kubernetes.io/part-of': 'stellar-atlas', 'purpose': 'isolated-restore'}}})
    pod = {'automountServiceAccountToken': False, 'containers': [{'name': 'postgres', 'image': lock()['images']['postgres:17-bookworm']['ref'],
        'env': [{'name': 'POSTGRES_PASSWORD_FILE', 'value': '/run/secrets/postgres_admin'}],
        'resources': {'requests': {'cpu': '50m', 'memory': '64Mi'}, 'limits': {'cpu': '1', 'memory': '512Mi'}},
        'volumeMounts': [{'name': 'secret', 'mountPath': '/run/secrets', 'readOnly': True}, {'name': 'data', 'mountPath': '/var/lib/postgresql/data'}],
        'readinessProbe': {'exec': {'command': ['pg_isready', '-U', 'postgres']}, 'periodSeconds': 2}}],
        'volumes': [{'name': 'secret', 'secret': {'secretName': 'postgres-admin'}}, {'name': 'data', 'emptyDir': {}}]}
    try:
        secret('postgres-admin', namespace, {'postgres_admin': (LOCAL / 'secrets/postgres_admin').read_text().strip()})
        apply({'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': 'restore', 'namespace': namespace}, 'spec': {'replicas': 1, 'selector': {'matchLabels': {'app': 'restore'}}, 'template': {'metadata': {'labels': {'app': 'restore'}}, 'spec': pod}}})
        kubectl('-n', namespace, 'rollout', 'status', 'deployment/restore', '--timeout=180s')
        target = {'namespace': namespace, 'deployment': 'restore'}
        for database, archive in record['databases'].items():
            if database not in ('stellar_catalog', 'stellar_journey') or archive['file'] != database + '.dump':
                raise ValueError('Unexpected backup database/path')
            raw = (directory / archive['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != archive['sha256']:
                raise ValueError('Backup checksum mismatch')
            db_exec('createdb', '-U', 'postgres', database, **target)
            db_exec('pg_restore', '-U', 'postgres', '-d', database, '--no-owner', '--no-privileges', '--exit-on-error', payload=raw, **target)
        count = int(sql('stellar_catalog', 'SELECT count(*) FROM catalog.stars', **target))
        active = sql('stellar_catalog', 'SELECT snapshot_id FROM catalog.active_snapshot', **target)
        row = sql('stellar_journey', "SELECT row_to_json(j)::text FROM journey.journeys j WHERE id='" + record['journey_id'] + "'", **target)
        if count != record['catalog_count'] or active != record['active_snapshot'] or hashlib.sha256(row.encode()).hexdigest() != record['journey_sha256']:
            raise ValueError('Isolated restored sample mismatch')
        from .application import http, smoke
        if json.loads(http('/api/journey/v1/journeys/' + record['journey_id'])[2]) != record['journey_http']:
            raise ValueError('Original working journey changed during isolated restore')
        smoke()
        return {'status': 'passed', 'isolated_namespace': namespace, 'catalog_count': count, 'active_snapshot': active,
            'journey_id': record['journey_id'], 'journey_row_sha256_matches': True, 'original_gateway_and_journey': 'passed', 'cleanup': 'only unique isolated namespace removed', 'backup': str(directory.relative_to(ROOT))}
    finally:
        kubectl('delete', 'namespace', namespace, '--wait=true', '--timeout=120s')


def monitoring_up():
    report = platform('runtime', do_apply=True, monitoring=True)
    for service in ('prometheus', 'grafana'):
        kubectl('-n', 'stellar-monitoring', 'rollout', 'status', 'deployment/' + service, '--timeout=180s')
    return report


def monitoring_check():
    require_cluster()
    from .application import http
    from urllib.parse import urlencode
    with forward('stellar-monitoring', 'prometheus', 9090) as port:
        base = 'http://127.0.0.1:' + str(port)
        query = '/api/v1/query?' + urlencode({'query': 'sum(stellar_http_requests_total{service="catalog",route="/v1/meta"})'})
        def count():
            results = json.loads(http(query, base=base)[2])['data']['result']
            return float(results[0]['value'][1]) if results else 0
        before = count()
        http('/api/catalog/v1/meta')
        for _ in range(20):
            time.sleep(1)
            after = count()
            if after > before:
                break
        else:
            raise ValueError('Gateway request did not appear in Prometheus')
        targets = json.loads(http('/api/v1/targets', base=base)[2])['data']['activeTargets']
        expected = set(r for r in running_release()['images'] if r not in ('web', 'importer'))
        actual = {t['labels']['instance'].split('.')[0] for t in targets}
        if actual != expected or any(t['health'] != 'up' for t in targets):
            raise ValueError('All running release API scrape targets must be up')
    with forward('stellar-monitoring', 'grafana', 3000) as port:
        base = 'http://127.0.0.1:' + str(port)
        password = (LOCAL / 'secrets/grafana_admin').read_text().strip()
        auth = {'Authorization': 'Basic ' + base64.b64encode(('admin:' + password).encode()).decode()}
        status, _, raw = http('/api/dashboards/uid/stellar-atlas', headers=auth, base=base)
        if status != 200 or len(json.loads(raw)['dashboard']['panels']) != 4:
            raise ValueError('Provisioned Grafana dashboard is unavailable')
    return {'status': 'passed', 'scrape_targets_up': len(expected), 'catalog_meta_requests_before': before, 'catalog_meta_requests_after': after, 'grafana_dashboard': 'stellar-atlas; four provisioned panels', 'access': 'loopback-only temporary port-forwards; stopped after check'}


def action(name, root='foundation', target=None):
    if name == 'cluster-create': return cluster_create()
    if name == 'platform-plan': return platform(root)
    if name == 'platform-apply': return platform(root, do_apply=True)
    if name == 'cluster-secrets': return cluster_secrets()
    if name == 'demo-bootstrap': return demo_bootstrap()
    if name == 'monitoring-up': return monitoring_up()
    if name == 'monitoring-check': return monitoring_check()
    if name == 'backup': return backup()
    if name == 'restore':
        if target != 'restore-check': raise ValueError('Only isolated --target restore-check is supported')
        return restore()
    raise ValueError('Unknown local Kubernetes action')
