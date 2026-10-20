"""Local application operations. No Kubernetes, publication or destructive teardown."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from uuid import uuid4
from .bootstrap import ROOT, LOCAL, write_json
from .guards import local_target
from .db import run

ROLES = ('web', 'catalog', 'journey', 'importer')

def source(clean=False):
    if clean and run(['git', 'status', '--porcelain']):
        raise ValueError('Release images require a clean source commit')
    return run(['git', 'rev-parse', 'HEAD'])

def stage_dataset():
    manifest = json.loads((ROOT / 'data/snapshot.lock.json').read_text())
    if manifest.get('fixture') is not False:
        raise ValueError('Local release images require the sealed real dataset')
    for name, notice in manifest['notices'].items():
        path = (ROOT / 'data' / name).resolve()
        if not path.is_relative_to((ROOT / 'data').resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != notice['sha256']:
            raise ValueError('Sealed data notice checksum mismatch')
    archive = LOCAL / 'data/sealed' / manifest['snapshot_id'] / 'gcns-required-fields.csv.gz'
    # No downloader or reseal: verify the preserved immutable bytes before the build context.
    if hashlib.sha256(archive.read_bytes()).hexdigest() != manifest['archive_sha256']:
        raise ValueError('Sealed archive checksum mismatch')
    with gzip.open(archive, 'rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['raw_sha256']:
            raise ValueError('Sealed raw checksum mismatch')
    target = local_target(LOCAL / 'images/dataset')
    target.mkdir(parents=True, exist_ok=True)
    allowed = {'catalog.csv.gz', 'snapshot.lock.json', *manifest['notices']}
    if any(p.relative_to(target).as_posix() not in allowed for p in target.rglob('*') if p.is_file()):
        raise ValueError('Unexpected file in isolated dataset build context')
    shutil.copyfile(archive, target / 'catalog.csv.gz')
    for name in ('snapshot.lock.json', *manifest['notices']):
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / 'data' / name, target / name)
    return target, manifest

def configure(sha):
    tag = 'local-' + sha[:12]
    (LOCAL / 'compose.env').write_text(f'IMAGE_TAG={tag}\nRELEASE_ID={tag}\n', encoding='utf-8')
    return tag

def images_build(clean=False):
    sha = source(clean)
    dataset, manifest = stage_dataset()
    tag = configure(sha)
    images = {}
    for role in ROLES:
        dockerfile = f'apps/web/Dockerfile' if role == 'web' else f'jobs/importer/Dockerfile' if role == 'importer' else f'services/{role}/Dockerfile'
        args = ['docker', 'build', '--provenance=false', '--build-arg', 'SOURCE_SHA=' + sha, '-f', dockerfile, '-t', f'stellar-atlas-{role}:{tag}']
        if role == 'importer':
            args += ['--build-context', 'dataset=' + str(dataset)]
        run(args + ['.'], timeout=1200)
        record = json.loads(run(['docker', 'image', 'inspect', f'stellar-atlas-{role}:{tag}']))[0]
        if record['Config']['Labels'].get('org.opencontainers.image.revision') != sha or record['Config']['User'] in ('', 'root', '0', '0:0'):
            raise ValueError('Image source/non-root check failed: ' + role)
        images[role] = {'ref': record['Id'], 'local_tag': f'stellar-atlas-{role}:{tag}', 'digest_kind': 'docker-image-id'}
    release = {'schema_version': 1, 'release_id': tag, 'source_sha': sha,
        'source_repository': 'Jyot-Kikani/DevOps_Assignment',
        'dataset': {'snapshot_id': manifest['snapshot_id'], 'raw_sha256': manifest['raw_sha256'], 'fixture': False}, 'images': images}
    write_json(LOCAL / 'release.json', release)
    return {'status': 'passed', 'source_sha': sha, 'clean_source': clean, 'images': images, 'publication': 'local only'}

def compose():
    if not (LOCAL / 'compose.env').is_file():
        raise ValueError('Run dev-up or images-build first')
    return ['docker', 'compose', '--env-file', str(LOCAL / 'compose.env'), '-f', str(ROOT / 'compose.yml'), '--profile', 'database']

def prepare_dsns():
    from .secrets import initialize, restrict
    from urllib.parse import quote
    initialize()
    for role, database in [('catalog_writer', 'stellar_catalog'), ('catalog_reader', 'stellar_catalog'), ('journey_owner', 'stellar_journey'), ('journey_app', 'stellar_journey')]:
        password = (LOCAL / 'secrets' / role).read_text().strip()
        path = LOCAL / 'secrets' / (role + '_dsn')
        path.write_text(f'postgresql+psycopg://{role}:{quote(password, safe="")}@postgres/{database}\n', encoding='utf-8')
        restrict(path)

def dev_up(build=True):
    prepare_dsns()
    if build:
        images_build()
    elif not (LOCAL / 'release.json').is_file():
        raise ValueError('Build images before --no-build startup')
    cmd = compose()
    run(cmd + ['up', '-d', '--wait', '--wait-timeout', '90', 'postgres'])
    for job in ('bootstrap', 'catalog-migrate', 'journey-migrate', 'importer'):
        run(cmd + ['--profile', 'jobs', 'run', '--rm', '--no-deps', job], timeout=600)
    run(cmd + ['up', '-d', '--wait', '--wait-timeout', '120', 'catalog', 'journey', 'web'])
    return smoke()

def http(path, body=None, headers=None, base='http://127.0.0.1:8080'):
    payload = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(base + path, data=payload, headers={'Content-Type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()

def smoke():
    release = json.loads((LOCAL / 'release.json').read_text())
    sha = release['source_sha']
    for path in ('/explore', '/journeys', '/saved', '/about'):
        status, _, body = http(path)
        if status != 200 or b'id="root"' not in body:
            raise ValueError('SPA deep-link smoke failed: ' + path)
    version = json.loads(http('/version.json')[2])
    if version['source_sha'] != sha or json.loads(http('/release.json')[2]) != release:
        raise ValueError('Web source/release metadata mismatch')
    for role in ('catalog', 'journey'):
        status, _, body = http(f'/api/{role}/v1/meta')
        meta = json.loads(body)
        if status != 200 or meta['source_sha'] != sha or meta['release_id'] != release['release_id'] or not meta['readiness']:
            raise ValueError('API identity/readiness failed: ' + role)
    status, _, body = http('/api/catalog/v1/snapshots/active')
    snapshot = json.loads(body)
    if status != 200 or snapshot['raw_sha256'] != release['dataset']['raw_sha256']:
        raise ValueError('Catalog dataset smoke failed')
    stars = json.loads(http(f'/api/catalog/v1/snapshots/{snapshot["snapshot_id"]}/stars?limit=1')[2])
    estimate_body = {'snapshot_id': snapshot['snapshot_id'], 'origin_id': 'sun', 'destination_id': stars['items'][0]['source_id'], 'speed_fraction_c': .1}
    status, _, body = http('/api/journey/v1/estimate', estimate_body)
    estimate = json.loads(body)
    if status != 200 or abs(estimate['duration_julian_years'] - estimate['distance_ly'] / .1) > 1e-9:
        raise ValueError('Journey estimate smoke failed')
    private = ['/metrics', '/docs', '/openapi.json', '/admin', '/api/catalog/metrics', '/api/catalog/health/ready',
        '/api/catalog/openapi.json', '/api/journey/docs', f'/api/catalog/v1/snapshots/{snapshot["snapshot_id"]}/positions']
    for path in private:
        if http(path)[0] != 404:
            raise ValueError('Gateway exposed private route: ' + path)
    # The service injects a fresh ID rather than trusting a visitor's value.
    _, headers, _ = http('/api/catalog/v1/meta', headers={'X-Request-ID': 'visitor-controlled'})
    if headers.get('X-Request-ID') == 'visitor-controlled':
        raise ValueError('Gateway did not replace public request ID')
    return {'status': 'passed', 'target': 'local', 'url': 'http://127.0.0.1:8080', 'source_sha': sha,
        'snapshot_id': snapshot['snapshot_id'], 'private_routes_checked': len(private), 'distance_ly': estimate['distance_ly']}

def persistence_check():
    snapshot = json.loads(http('/api/catalog/v1/snapshots/active')[2])
    stars = json.loads(http(f'/api/catalog/v1/snapshots/{snapshot["snapshot_id"]}/stars?limit=1')[2])
    status, _, raw = http('/api/journey/v1/journeys', {'snapshot_id': snapshot['snapshot_id'], 'origin_id': 'sun',
        'destination_id': stars['items'][0]['source_id'], 'speed_fraction_c': .1}, {'Idempotency-Key': str(uuid4())})
    if status != 201:
        raise ValueError('Persistence share creation failed')
    journey = json.loads(raw)
    run(compose() + ['restart', 'postgres', 'catalog', 'journey', 'web'])
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        try:
            if http('/api/journey/v1/journeys/' + journey['id'])[2] == raw:
                report = smoke()
                report.update(journey_id=journey['id'], restart='PostgreSQL and all three runtime containers; identical persisted journey')
                return report
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise ValueError('Persisted journey not recovered after restart')

def action(name, no_build=False):
    if name == 'dev-up':
        return dev_up(build=not no_build)
    if name == 'dev-down':
        run(compose() + ['stop'])
        return {'status': 'passed', 'scope': 'project containers stopped; named volume and unrelated resources preserved'}
    if name == 'smoke':
        return smoke()
    if name == 'compose-check':
        return persistence_check()
    return images_build(clean=True)
