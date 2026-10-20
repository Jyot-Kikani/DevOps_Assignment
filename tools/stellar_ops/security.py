"""Course-sized checks: existing security gate, one fake rejection, Grype images."""
import json
import os
import subprocess
import sys
from .bootstrap import ROOT, LOCAL, find_tool, write_json

def fake_rejection():
    # Deliberately fake; never an account credential and never committed as a token.
    text = 'github_token = "' + 'ghp_' + ('Ab12Cd34Ef56' * 3) + '"\n'
    result = subprocess.run([find_tool('gitleaks'), 'stdin', '--redact', '--no-banner', '--exit-code', '1'], input=text,
        capture_output=True, text=True, cwd=ROOT, timeout=30)
    write_json(LOCAL / 'reports/fake-secret-rejection.json', {'expected_exit_code': 1, 'exit_code': result.returncode,
        'stderr': result.stderr, 'fixture': 'clearly fake GitHub-shaped token generated only in process memory'})
    if result.returncode != 1 or 'leaks found' not in result.stderr.lower():
        raise ValueError('Fake secret detector demonstration did not reject the fixture')
    return {'status': 'passed', 'expected_rejection': True, 'exit_code': result.returncode}

def image_scan():
    release = json.loads((LOCAL / 'release.json').read_text())
    tool = find_tool('grype')
    if not tool:
        raise ValueError('Restore the pinned Grype tool first')
    version = subprocess.check_output([tool, 'version'], cwd=ROOT, text=True, timeout=20)
    expected = json.loads((ROOT / 'tools/toolchain.lock.json').read_text())['tools']['grype']['version']
    if expected not in version:
        raise ValueError('Grype version differs from the frozen tool')
    env = os.environ.copy()
    env.update(GRYPE_DB_CACHE_DIR=str(LOCAL / 'grype-db'), GRYPE_CHECK_FOR_APP_UPDATE='false')
    results = {}
    for role, image in release['images'].items():
        directory = LOCAL / 'reports/image-scans'
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / (role + '-' + image['ref'].split(':')[-1][:12] + '.json')
        with target.open('w', encoding='utf-8') as output, target.with_suffix('.log').open('w', encoding='utf-8') as log:
            result = subprocess.run([tool, '--from', 'docker', image['ref'], '--fail-on', 'high', '-o', 'json'], cwd=ROOT, env=env,
                stdout=output, stderr=log, timeout=600)
        scan = json.loads(target.read_text(encoding='utf-8'))
        severities = {}
        for finding in scan.get('matches', []):
            severity = finding['vulnerability']['severity']
            severities[severity] = severities.get(severity, 0) + 1
        results[role] = {'exit_code': result.returncode, 'image_ref': image['ref'], 'findings': severities, 'report': str(target.relative_to(ROOT))}
    report = {'status': 'passed' if all(r['exit_code'] == 0 for r in results.values()) else 'failed', 'scanner': 'Grype ' + expected,
        'source_sha': release['source_sha'], 'threshold': 'high', 'images': results}
    write_json(LOCAL / 'reports/image-scan.json', report)
    return report

def security():
    subprocess.run([sys.executable, 'tools/ci_security.py', '--json'], cwd=ROOT, check=True, timeout=240, capture_output=True)
    rejected = fake_rejection()
    report = image_scan()
    report['fake_secret_rejection'] = rejected
    report['existing_secret_and_publication_checks'] = 'passed'
    return report
