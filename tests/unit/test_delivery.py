"""Focused publication boundaries and stale-main rejection; live evidence is separate."""
import json
import pytest
import release
from stellar_ops import delivery, data


def record():
    return {'release_id': 'r1-a1-' + 'a' * 12, 'source_sha': 'a' * 40,
        'dataset': {'snapshot_id': 'gcns-test'},
        'images': {r: {'ref': f'ghcr.io/jyot-kikani/stellar-atlas-{r}@sha256:' + 'b' * 64,
            'manifest_digest': 'sha256:' + 'b' * 64} for r in release.ROLES}}


def test_deploy_contains_only_scoped_application_objects():
    objects = release.render_release(record())['items']
    allowed = {'Service', 'Deployment', 'ConfigMap', 'CronJob'}
    assert all(x['kind'] in allowed and x['metadata']['namespace'] == 'stellar-atlas' for x in objects)
    assert all('IMAGE_' not in json.dumps(x) for x in objects)
    for obj in objects:
        if obj['kind'] == 'Deployment':
            container = obj['spec']['template']['spec']['containers'][0]
            assert container['image'].startswith('ghcr.io/jyot-kikani/')
            assert '@sha256:' in container['image'] and container['imagePullPolicy'] == 'IfNotPresent'


def test_no_promotion_from_stale_or_failed_main(monkeypatch):
    sha = 'a' * 40
    monkeypatch.setattr(release, 'api', lambda path: {'object': {'sha': 'b' * 40}})
    with pytest.raises(ValueError, match='latest main'):
        release.current_main(sha)
    monkeypatch.setattr(release, 'api', lambda path: {'object': {'sha': sha}} if '/git/ref/' in path else
        {'check_runs': [{'id': 1, 'name': 'ci / quality', 'conclusion': 'failure'}]})
    with pytest.raises(ValueError, match='CI not successful'):
        release.current_main(sha)


def test_publisher_rejects_other_repositories():
    with pytest.raises(ValueError, match='canonical'):
        data.publish_github(None, {}, 'Someone/DevOps_Assignment', {})


def test_public_smoke_rejects_other_tunnel_hosts(monkeypatch, tmp_path):
    monkeypatch.setattr(delivery, 'TUNNEL', tmp_path)
    (tmp_path / 'state.json').write_text(json.dumps({'url': 'https://example.com'}))
    with pytest.raises(ValueError, match='Quick Tunnel'):
        delivery.public_url()


def test_argo_scope_excludes_platform_and_secrets():
    project = json.loads((delivery.ROOT / 'infra/argocd/project.json').read_text())['spec']
    assert project['clusterResourceWhitelist'] == []
    assert project['destinations'] == [{'server': 'https://kubernetes.default.svc', 'namespace': 'stellar-atlas'}]
    assert 'Secret' not in [x['kind'] for x in project['namespaceResourceWhitelist']]


def test_recovery_records_running_gitops_release(monkeypatch):
    from stellar_ops import application, kubernetes
    expected = {**record(), 'source_dirty': False, 'dataset': {'fixture': False, 'snapshot_id': 'gcns-test'}}
    monkeypatch.setattr(application, 'http', lambda path: (200, {}, json.dumps(
        expected if path == '/release.json' else {'source_sha': expected['source_sha']}).encode()))
    assert kubernetes.running_release() == expected
