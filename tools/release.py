"""P15 trusted-main image build, truthful Grype review, publication and Git promotion."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import urllib.request

from stellar_ops.bootstrap import ROOT, LOCAL, digest, find_tool, write_json
from stellar_ops.github import REPOSITORY, api
from stellar_ops.kubernetes import render

ROLES = ('web', 'catalog', 'journey', 'importer')


def run(args, *, env=None, payload=None, timeout=1200):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, input=payload, env=env,
        capture_output=True, timeout=timeout)
    directory = LOCAL / 'reports/release'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f'{len(list(directory.glob("*.log"))):03d}.log').write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError('Release operation failed: ' + result.stderr.decode(errors='replace')[-1500:])
    return result.stdout.decode().strip()


def download(url, path, expected):
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as source, path.open('wb') as target:
        while block := source.read(1024 * 1024):
            target.write(block)
    if digest(path) != expected:
        raise ValueError('Public asset checksum mismatch: ' + path.name)


def dataset():
    """Anonymous real release download; frozen provenance files are never rewritten."""
    from stellar_ops.data import ARCHIVE, RELEASE, fetch_extract
    lock = json.loads((ROOT / 'data/snapshot.lock.json').read_text())
    url = f'https://github.com/{REPOSITORY}/releases/download/{RELEASE}/'
    directory = LOCAL / 'images/dataset'
    directory.mkdir(parents=True, exist_ok=True)
    download(url + ARCHIVE, directory / 'catalog.csv.gz', lock['archive_sha256'])
    for name in ('snapshot.lock.json', *lock['notices']):
        expected = digest(ROOT / 'data' / name)
        download(url + Path(name).name, directory / name, expected)
    # Verify decompressed bytes as well, without retaining another copy.
    import gzip
    with gzip.open(directory / 'catalog.csv.gz', 'rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != lock['raw_sha256']:
            raise ValueError('Public raw dataset checksum mismatch')
    return directory, lock


def build(sha, directory, tag):
    images = {}
    for role in ROLES:
        dockerfile = 'apps/web/Dockerfile' if role == 'web' else 'jobs/importer/Dockerfile' if role == 'importer' else f'services/{role}/Dockerfile'
        ref = f'stellar-atlas-{role}:{tag}'
        args = ['docker', 'buildx', 'build', '--load', '--provenance=false', '--build-arg', 'SOURCE_SHA=' + sha,
            '-f', dockerfile, '-t', ref]
        if role == 'importer':
            args += ['--build-context', 'dataset=' + str(directory)]
        run(args + ['.'])
        record = json.loads(run(['docker', 'image', 'inspect', ref]))[0]
        if record['Config']['Labels']['org.opencontainers.image.revision'] != sha or record['Config']['User'] in ('', '0', 'root', '0:0'):
            raise ValueError('Image source/non-root mismatch: ' + role)
        images[role] = ref
    return images


def scanner():
    lock = json.loads((ROOT / 'tools/toolchain.lock.json').read_text())
    if os.name == 'nt':
        return find_tool('grype')
    entry = lock['tools_linux']['grype']
    directory = LOCAL / 'tools/release-grype'
    archive = directory / 'grype.tar.gz'
    download(entry['url'], archive, entry['sha256'])
    executable = directory / 'grype'
    with tarfile.open(archive) as bundle:
        member = bundle.getmember('grype')
        if not member.isfile():
            raise ValueError('Invalid Grype executable archive')
        executable.write_bytes(bundle.extractfile(member).read())
    executable.chmod(0o755)
    return str(executable)


def scan(images, sha):
    tool = scanner()
    expected = json.loads((ROOT / 'tools/toolchain.lock.json').read_text())['tools']['grype']['version']
    if expected not in run([tool, 'version']):
        raise ValueError('Grype differs from pinned version')
    env = os.environ.copy()
    env.update(GRYPE_DB_CACHE_DIR=str(LOCAL / 'grype-db'), GRYPE_CHECK_FOR_APP_UPDATE='false')
    summary = {'source_sha': sha, 'scanner': 'Grype ' + expected, 'threshold': 'high', 'images': {}}
    for role, ref in images.items():
        path = LOCAL / f'reports/release/grype-{role}.json'
        with path.open('wb') as output, path.with_suffix('.log').open('wb') as log:
            result = subprocess.run([tool, '--from', 'docker', ref, '--fail-on', 'high', '-o', 'json'],
                env=env, cwd=ROOT, stdout=output, stderr=log, timeout=600)
        if result.returncode not in (0, 2):
            raise ValueError('Grype failed to scan ' + role)
        findings = json.loads(path.read_text())['matches']
        counts = {}
        for finding in findings:
            severity = finding['vulnerability']['severity']
            counts[severity] = counts.get(severity, 0) + 1
        summary['images'][role] = {'exit_code': result.returncode, 'findings': counts}
    summary['status'] = 'failed' if any(i['exit_code'] for i in summary['images'].values()) else 'passed'
    summary['publication_policy'] = 'ADR 0005: scan/review/documentation; strict threshold is retained, not a publication prerequisite. See docs/P10_IMAGE_REVIEW.md.'
    write_json(LOCAL / 'reports/release/scan-summary.json', summary)
    if summary['status'] == 'failed':
        print('::warning::Grype high threshold failed; findings preserved in scan-summary.json under ADR 0005')
    return summary


def anonymous_images(record):
    """Verify registry manifests without any saved Docker/GitHub credential."""
    for role, image in record['images'].items():
        repository = f'jyot-kikani/stellar-atlas-{role}'
        url = 'https://ghcr.io/token?service=ghcr.io&scope=repository:' + repository + ':pull'
        with urllib.request.urlopen(url, timeout=30) as response:
            token = json.load(response)['token']
        request = urllib.request.Request(f'https://ghcr.io/v2/{repository}/manifests/{image["manifest_digest"]}',
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            if hashlib.sha256(response.read()).hexdigest() != image['manifest_digest'].split(':')[1]:
                raise ValueError('Anonymous registry digest mismatch: ' + role)


def render_release(record, name='app.json'):
    """Only application objects; platform, secrets and database never enter deploy."""
    app = render(name, record)
    refs = {f'docker.io/library/stellar-atlas-{role}@{image["manifest_digest"]}': image['ref'] for role, image in record['images'].items()}
    def convert(value):
        if isinstance(value, dict):
            return {key: 'IfNotPresent' if key == 'imagePullPolicy' else convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        return refs.get(value, value) if isinstance(value, str) else value
    objects = convert(app)['items']
    if name == 'app.json':
        objects.append({'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'release', 'namespace': 'stellar-atlas'},
            'data': {'release.json': json.dumps(record)}})
    return {'apiVersion': 'v1', 'kind': 'List', 'items': objects}


def current_main(sha):
    if api(f'repos/{REPOSITORY}/git/ref/heads/main')['object']['sha'] != sha:
        raise ValueError('Source is no longer latest main; no deploy promotion')
    checks = api(f'repos/{REPOSITORY}/commits/{sha}/check-runs')['check_runs']
    for name in ('ci / quality', 'ci / security'):
        matching = [c for c in checks if c['name'] == name]
        if not matching or max(matching, key=lambda c: c['id'])['conclusion'] != 'success':
            raise ValueError('Required current-head CI not successful: ' + name)


def publish():
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or os.environ.get('GITHUB_REF') != 'refs/heads/main':
        raise ValueError('Publication runs only in the canonical trusted main workflow')
    sha = run(['git', 'rev-parse', 'HEAD'])
    if run(['git', 'status', '--porcelain']):
        raise ValueError('Release source must be clean')
    current_main(sha)
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_run':
        changed = api(f'repos/{REPOSITORY}/commits/{sha}')['files']
        # A final evidence-only merge must not undo the demonstrated deploy rollback.
        if changed and len(changed) < 300 and all(f['filename'].startswith('docs/') or f['filename'] in ('README.md', 'CONTRIBUTING.md', 'AGENTS.md') for f in changed):
            print('Documentation-only main commit; existing deployment preserved. Manual dispatch can publish explicitly.')
            return
    directory, lock = dataset()
    tag = f'r{os.environ["GITHUB_RUN_ID"]}-a{os.environ["GITHUB_RUN_ATTEMPT"]}-{sha[:12]}'
    images = build(sha, directory, tag)
    summary = scan(images, sha)
    env = os.environ.copy()
    # Credentials only via stdin and an ignored ephemeral Docker config.
    env['DOCKER_CONFIG'] = str(LOCAL / 'release-docker')
    run(['docker', 'login', 'ghcr.io', '--username', os.environ['GITHUB_ACTOR'], '--password-stdin'],
        env=env, payload=os.environ['GH_TOKEN'].encode())
    record = {'schema_version': 1, 'release_id': tag, 'source_sha': sha, 'source_repository': REPOSITORY,
        'source_dirty': False, 'created_at': datetime.now(timezone.utc).isoformat(),
        'dataset': {'snapshot_id': lock['snapshot_id'], 'raw_sha256': lock['raw_sha256'], 'fixture': False},
        'compatibility': {'catalog_schema': 1, 'journey_schema': 1, 'model': 'constant-speed-v1'}, 'images': {}}
    try:
        for role, local in images.items():
            registry = f'ghcr.io/jyot-kikani/stellar-atlas-{role}'
            target = registry + ':' + tag
            run(['docker', 'tag', local, target])
            output = run(['docker', 'push', target], env=env)
            matches = re.findall(r'digest: (sha256:[a-f0-9]{64})', output)
            if not matches:
                raise ValueError('Registry did not return a pushed manifest digest')
            value = matches[-1]
            record['images'][role] = {'ref': registry + '@' + value, 'manifest_digest': value}
    finally:
        run(['docker', 'logout', 'ghcr.io'], env=env)
    from schema_models import Release
    Release.model_validate(record)
    write_json(LOCAL / 'published-release.json', record)
    anonymous_images(record)
    current_main(sha)
    # Orphan deploy branch contains only generated application manifests/metadata.
    checkout = LOCAL / 'deploy-work'
    checkout.mkdir(parents=True, exist_ok=False)
    def git(*args):
        return run(['git', '-C', checkout, *args], env=env)
    git('init', '-b', 'deploy')
    git('remote', 'add', 'origin', f'https://github.com/{REPOSITORY}.git')
    # Avoid credentials in command arguments, files or remote URLs.
    import base64
    authorization = base64.b64encode(('x-access-token:' + os.environ['GH_TOKEN']).encode()).decode()
    env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader', GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + authorization)
    refs = git('ls-remote', '--heads', 'origin', 'deploy')
    if refs:
        git('fetch', '--depth=1', 'origin', 'deploy')
        git('checkout', '-B', 'deploy', 'FETCH_HEAD')
    write_json(checkout / 'app/app.json', render_release(record))
    write_json(checkout / 'release.json', record)
    write_json(checkout / 'scan-summary.json', summary)
    git('config', 'user.name', 'github-actions[bot]')
    git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    git('add', 'app/app.json', 'release.json', 'scan-summary.json')
    git('commit', '-m', 'Deploy ' + tag)
    current_main(sha)
    git('push', 'origin', 'HEAD:deploy')
    print(json.dumps({'status': 'published', 'release': record, 'deployment': 'pending local Argo verification'}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build-check', 'publish', 'data-check'])
    args = parser.parse_args()
    if args.action == 'publish':
        publish()
    elif args.action == 'data-check':
        directory, lock = dataset()
        print(json.dumps({'status': 'passed', 'anonymous': True, 'snapshot_id': lock['snapshot_id'], 'archive_sha256': lock['archive_sha256']}))
    else:
        directory = LOCAL / 'images/ci-build-context'
        directory.mkdir(parents=True, exist_ok=True)
        (directory / 'README.txt').write_text('Build-only CI context. Not a runnable or publishable catalog.')
        build(run(['git', 'rev-parse', 'HEAD']), directory, 'ci-build')
        print('Four non-root images built; importer context is build-only, no publication.')


if __name__ == '__main__':
    main()
