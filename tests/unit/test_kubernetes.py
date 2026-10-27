"""Focused manifest/restore boundary checks; live phase evidence is recorded separately."""
import json

import pytest

from stellar_ops import kubernetes as k


def prepared():
    return {'release_id': 'local-' + 'a' * 12, 'source_sha': 'a' * 40,
        'dataset': {'snapshot_id': 'gcns-test'}, 'images': {r: {'manifest_digest': 'sha256:' + 'b' * 64} for r in ('web', 'catalog', 'search', 'atlas-map', 'snapshot', 'calculation', 'journey', 'importer')}}


def test_runtime_identity_and_private_services():
    app = k.render('app.json', prepared())['items']
    deployments = [x for x in app if x['kind'] == 'Deployment']
    assert {x['metadata']['name'] for x in deployments} == {'web', 'catalog', 'search', 'atlas-map', 'snapshot', 'calculation', 'journey'}
    for deployment in deployments:
        spec = deployment['spec']['template']['spec']
        container = spec['containers'][0]
        env = {x['name']: x['value'] for x in container['env']}
        assert env['RELEASE_ID'] == prepared()['release_id']
        assert env['CATALOG_SNAPSHOT_ID'] == 'gcns-test'
        assert spec['securityContext']['runAsNonRoot']
        assert spec['automountServiceAccountToken'] is False
        assert '@sha256:' in container['image'] and container['imagePullPolicy'] == 'Never'
        assert all(key in container for key in ('resources', 'readinessProbe', 'livenessProbe'))
    services = [x for x in app if x['kind'] == 'Service']
    assert [x['metadata']['name'] for x in services if x['spec']['type'] == 'NodePort'] == ['web']
    calculation = next(x for x in deployments if x['metadata']['name'] == 'calculation')['spec']['template']['spec']
    assert 'volumes' not in calculation
    assert all('DSN' not in env['name'] for env in calculation['containers'][0]['env'])
    jobs = k.render('jobs.json', prepared())['items']
    assert [x['metadata']['name'] for x in jobs] == ['bootstrap', 'catalog-migrate', 'journey-migrate', 'importer']
    cron = next(x for x in app if x['kind'] == 'CronJob')
    assert cron['spec']['timeZone'] == 'Etc/UTC'
    assert cron['spec']['jobTemplate']['spec']['template']['spec']['volumes'][0]['secret']['secretName'] == 'journey-app'


def test_secret_payload_is_stdin_only(monkeypatch):
    calls = []
    monkeypatch.setattr(k, 'kubectl', lambda *args, **kwargs: calls.append((args, kwargs)))
    k.secret('test', 'stellar-atlas', {'password': 'only-a-test-value'})
    args, kwargs = calls[0]
    assert 'only-a-test-value' not in str(args)
    assert kwargs['private'] is True
    assert 'stringData' not in json.loads(kwargs['payload'])


def test_restore_requires_isolated_target():
    with pytest.raises(ValueError, match='isolated'):
        k.action('restore', target='stellar-data')


def test_terraform_contains_no_secret_resources():
    for root in ('foundation', 'runtime'):
        document = json.loads((k.ROOT / f'infra/terraform/{root}/main.tf.json').read_text())
        assert not any('secret' in name for name in document['resource'])
        assert document['provider']['kubernetes']['config_context'] == k.CONTEXT
    foundation = json.loads((k.ROOT / 'infra/terraform/foundation/main.tf.json').read_text())
    assert foundation['resource']['kubernetes_persistent_volume_claim_v1']['postgres']['lifecycle']['prevent_destroy']


def test_restart_waits_for_gateway_endpoint_propagation(monkeypatch):
    import check_kubernetes as checks
    sample = {'journey_id': 'test', 'journey_http': {'id': 'test', 'distance_ly': 4.2}}
    responses = iter([(502, {}, b'<html>upstream unavailable</html>'), (200, {}, json.dumps(sample['journey_http']).encode())])
    monkeypatch.setattr(checks, 'http', lambda path: next(responses))
    monkeypatch.setattr(checks.time, 'sleep', lambda seconds: None)
    checks.wait_for_journey(sample)
