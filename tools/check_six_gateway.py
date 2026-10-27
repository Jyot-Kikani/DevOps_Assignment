"""Check production Nginx routing against six fixture-backed service images.

Run after db-check, check_web_ci and release.py build-check. Uses the existing
test database and a separate Compose project; never imports data or publishes.
"""
import json
import os
import subprocess
from uuid import uuid4

from stellar_ops.bootstrap import ROOT, LOCAL, write_json
from stellar_ops.application import http, prepare_dsns

APIS = ('catalog', 'search', 'atlas-map', 'snapshot', 'calculation', 'journey')
BASE = 'http://127.0.0.1:18080'


def run(args, env=None):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env,
        capture_output=True, text=True, encoding='utf-8', timeout=180)
    if result.returncode:
        raise ValueError('Gateway check operation failed: ' + result.stderr[-2000:])
    return result.stdout.strip()


def main():
    prepare_dsns()
    sha = json.loads(run(['docker', 'image', 'inspect', 'stellar-atlas-web:ci-build']))[0]['Config']['Labels']['org.opencontainers.image.revision']
    database = run(['docker', 'compose', '-f', 'compose.database.yml', '--profile', 'database', 'ps', '-q', 'postgres'])
    if not database:
        raise ValueError('Start the local test database and load the CI fixture first')
    sid = run(['docker', 'exec', database, 'psql', '-U', 'postgres', '-d', 'stellar_catalog', '-At', '-c', 'SELECT snapshot_id FROM catalog.active_snapshot'])
    if not sid.startswith('fixture-'):
        raise ValueError('Gateway fixture check requires an active CI fixture, not the demo dataset')
    env = os.environ.copy()
    env.update(IMAGE_TAG='ci-build', RELEASE_ID='local-' + sha[:12], APP_ENV='ci')
    # Existing DSN files are private inputs. No credential values are read here.
    document = json.loads(run(['docker', 'compose', '-f', 'compose.yml', '--profile', 'database', 'config', '--format', 'json'], env))
    document['name'] = 'stellar-atlas-six-check'
    document['services'] = {r: document['services'][r] for r in (*APIS, 'web')}
    document['networks'] = {'default': {'external': True, 'name': 'stellar-atlas-db_default'}}
    document.pop('volumes', None)
    for role, service in document['services'].items():
        service['restart'] = 'no'
        service['depends_on'] = {k:v for k,v in service.get('depends_on', {}).items() if k in document['services']}
        if role != 'web':
            service['environment']['CATALOG_SNAPSHOT_ID'] = sid
    release_path = LOCAL / 'six-check-release.json'
    write_json(release_path, {'source_sha': sha, 'release_id': 'local-' + sha[:12],
        'source_repository': 'Jyot-Kikani/DevOps_Assignment', 'dataset': {'snapshot_id': sid, 'fixture': True}})
    web = document['services']['web']
    web['ports'] = [{'target':8080, 'published':'18080', 'host_ip':'127.0.0.1', 'protocol':'tcp'}]
    web['volumes'] = [{'type':'bind', 'source':str(release_path), 'target':'/etc/stellar/release.json', 'read_only':True}]
    config = LOCAL / 'six-check-compose.json'
    write_json(config, document)
    cmd = ['docker', 'compose', '-f', str(config)]
    try:
        run(cmd + ['up', '-d', '--wait', '--wait-timeout', '90'])
        def request(path, body=None, headers=None):
            return http(path, body, headers, base=BASE)
        for role in APIS:
            status, _, raw = request(f'/api/{role}/v1/meta')
            meta = json.loads(raw)
            if status != 200 or not meta['readiness'] or meta['service'] != role.replace('-', '_'):
                raise ValueError('Gateway metadata route failed: ' + role)
        prefix = '/api/catalog/v1/snapshots/' + sid
        for path in ('/api/catalog/v1/snapshots/active', prefix, prefix + '/stars?limit=1',
                     prefix + '/stars/sun', prefix + '/stars/sun/neighbors', prefix + '/map'):
            if request(path)[0] != 200:
                raise ValueError('Production gateway route failed: ' + path)
        manifest = json.loads(request(prefix + '/map')[2])
        status, headers, binary = request(manifest['chunks'][0]['url'])
        if status != 200 or headers.get('Content-Encoding') != 'gzip' or not binary:
            raise ValueError('Production binary map route failed')
        body = {'snapshot_id':sid, 'origin_id':'sun', 'destination_id':'5853498713190525696', 'speed_fraction_c':.1}
        if request('/api/journey/v1/estimate', body)[0] != 200:
            raise ValueError('Production Calculation route failed')
        status, _, raw = request('/api/journey/v1/journeys', body, {'Idempotency-Key':str(uuid4())})
        if status != 201 or request('/api/journey/v1/journeys/' + json.loads(raw)['id'])[2] != raw:
            raise ValueError('Production shared journey round trip failed')
        private = ['/metrics', '/docs', prefix + '/positions']
        private += [f'/api/{role}/{suffix}' for role in APIS for suffix in ('metrics', 'docs', 'health/ready')]
        if any(request(path)[0] != 404 for path in private):
            raise ValueError('Production gateway exposed a private route')
        write_json(LOCAL / 'reports/six-gateway.json', {'status':'passed', 'backend_services':list(APIS),
            'fixture':True, 'private_routes_checked':len(private), 'scope':'local production Nginx and all six API images; no publication'})
        print('Production gateway and six backend images passed; 21 private routes denied.')
    finally:
        run(cmd + ['stop', '--timeout', '10'])


if __name__ == '__main__':
    main()
