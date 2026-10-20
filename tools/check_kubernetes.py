"""Focused live P12/P13 demonstrations; never delete clusters or working data."""
import argparse
import json
import time

from stellar_ops import kubernetes as k
from stellar_ops.application import http, smoke
from stellar_ops.bootstrap import LOCAL, ROOT, write_json


def wait_for_journey(recovery):
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        status, _, raw = http('/api/journey/v1/journeys/' + recovery['journey_id'])
        if status == 200:
            if json.loads(raw) != recovery['journey_http']:
                raise ValueError('Shared journey changed after workload replacement')
            return
        if status not in (502, 503, 504):
            raise ValueError(f'Unexpected journey response after restart: {status}')
        time.sleep(1)
    raise ValueError('Gateway did not recover after workload replacement')


def platform():
    k.require_cluster()
    k.kubectl('-n', 'stellar-data', 'rollout', 'status', 'deployment/postgres', '--timeout=180s')
    plans = {root: k.platform(root) for root in ('foundation', 'runtime')}
    if any(p['changes'] for p in plans.values()):
        raise ValueError('Baseline must have no Terraform changes')
    k.kubectl('label', 'namespace', 'stellar-atlas', 'demo=drift-demo', '--overwrite')
    try:
        detected = k.platform('foundation')
        if not detected['changes']:
            raise ValueError('Terraform did not detect namespace label drift')
    finally:
        k.platform('foundation', do_apply=True)
    repaired = k.platform('foundation')
    if repaired['changes']:
        raise ValueError('Terraform drift repair did not converge')
    return {'status': 'passed', 'phase': 'P12', 'baseline_plans': plans, 'label_drift_detected': True,
        'repaired_plan_no_changes': True, 'postgres_ready': True,
        'storage': json.loads(k.kubectl('get', 'storageclass', 'standard', '-o', 'json'))['provisioner']}


def application():
    k.require_cluster()
    report = smoke()
    sid = report['snapshot_id']
    counts = json.loads(http('/api/catalog/v1/snapshots/active')[2])['counts']
    sealed = json.loads((ROOT / 'data/snapshot.lock.json').read_text())['counts']
    if counts != {'total': sealed['rows'], 'within_100pc': sealed['within_100pc'], 'within_50ly': sealed['within_50ly'], 'within_25ly': sealed['within_25ly']}:
        raise ValueError('Gateway counts differ from sealed snapshot')
    recovery = k.sample()
    before = json.loads(k.kubectl('-n', 'stellar-atlas', 'get', 'pods', '-l', 'app=journey', '-o', 'json'))['items'][0]['metadata']['uid']
    start = time.monotonic()
    k.kubectl('-n', 'stellar-atlas', 'rollout', 'restart', 'deployment/journey')
    k.kubectl('-n', 'stellar-atlas', 'rollout', 'status', 'deployment/journey', '--timeout=180s')
    wait_for_journey(recovery)
    elapsed = round(time.monotonic() - start, 3)
    after = {p['metadata']['uid'] for p in json.loads(k.kubectl('-n', 'stellar-atlas', 'get', 'pods', '-l', 'app=journey', '-o', 'json'))['items'] if not p['metadata'].get('deletionTimestamp')}
    if before in after:
        raise ValueError('Journey workload was not replaced')
    if k.sql('stellar_catalog', 'SELECT count(*) FROM catalog.stars') != str(counts['total']):
        raise ValueError('Database/gateway count mismatch')
    cron = json.loads(k.kubectl('-n', 'stellar-atlas', 'get', 'cronjob/journey-retention', '-o', 'json'))
    job = {'apiVersion': 'batch/v1', 'kind': 'Job', 'metadata': {'name': 'retention-check', 'namespace': 'stellar-atlas'}, 'spec': cron['spec']['jobTemplate']['spec']}
    k.run_job(job)
    smoke()
    report.update(phase='P13', counts=counts, dns='Journey→Catalog and private DB cross-namespace DNS passed',
        journey_id=recovery['journey_id'], identical_share_after_restart=True, replacement_seconds=elapsed,
        retention_job='daily UTC schedule installed; manual execution passed')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['platform', 'application'], required=True)
    arguments = parser.parse_args()
    try:
        report = platform() if arguments.phase == 'platform' else application()
    except Exception as error:
        report = {'status': 'failed', 'error': str(error)}
    write_json(LOCAL / 'reports' / ('p12-check.json' if arguments.phase == 'platform' else 'p13-check.json'), report)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'passed' else 1)
