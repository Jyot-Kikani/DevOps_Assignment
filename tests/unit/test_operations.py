"""Focused lifecycle safety and recovery regressions; real demo evidence is separate."""
import json
import pytest

from stellar_ops import operations as ops


def expected_node():
    return {'Id': 'existing-node', 'Name': '/' + ops.NODE, 'State': {'Running': True},
        'Config': {'Image': 'kindest/node@sha256:test', 'Labels': {
            'io.x-k8s.kind.cluster': ops.k.CLUSTER, 'io.x-k8s.kind.role': 'control-plane'}},
        'HostConfig': {'PortBindings': {'30080/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '8080'}],
            '6443/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '12345'}]}}}


@pytest.mark.parametrize('change', ['cluster', 'image', 'public-api', 'public-web'])
def test_refuses_unexpected_container_before_mutation(monkeypatch, change):
    info = expected_node()
    if change == 'cluster':
        info['Config']['Labels']['io.x-k8s.kind.cluster'] = 'another-cluster'
    elif change == 'image':
        info['Config']['Image'] = 'kindest/node@sha256:other'
    else:
        port = '6443/tcp' if change == 'public-api' else '30080/tcp'
        info['HostConfig']['PortBindings'][port][0]['HostIp'] = '0.0.0.0'
    calls = []
    monkeypatch.setattr(ops.k, 'execute', lambda args: calls.append(args) or json.dumps([info]))
    monkeypatch.setattr(ops.k, 'lock', lambda: {'images': {'kindest/node:v1.35.8': {'digest': 'sha256:test'}}})
    with pytest.raises(ValueError, match='Unexpected project node'):
        ops.demo_stop()
    assert calls == [['docker', 'inspect', ops.NODE]]


def test_start_rejects_replaced_node_before_starting(monkeypatch, tmp_path):
    state = tmp_path / 'state.json'
    state.write_text(json.dumps({'node_id': 'old-node'}))
    monkeypatch.setattr(ops, 'STATE', state)
    monkeypatch.setattr(ops, 'node', expected_node)
    with pytest.raises(ValueError, match='Saved node identity differs'):
        ops.demo_start()
    assert state.exists()


def test_repeated_stop_preserves_checkpoint(monkeypatch, tmp_path):
    state = tmp_path / 'state.json'
    state.write_text('original checkpoint')
    monkeypatch.setattr(ops, 'STATE', state)
    monkeypatch.setattr(ops, 'node', lambda: {'State': {'Running': False}})
    closed = []
    monkeypatch.setattr(ops.delivery, 'public_stop', lambda: closed.append(True))
    assert ops.demo_stop()['already_stopped']
    assert state.read_text() == 'original checkpoint'
    assert closed == [True]


def test_gateway_retries_transport_and_upstream_failure_but_rejects_changed_data(monkeypatch):
    saved = {'sample': {'journey_id': 'test', 'journey_http': {'id': 'test', 'distance_ly': 4.2}}}
    responses = iter([OSError('connection refused'), (502, {}, b'unavailable'),
        (200, {}, json.dumps(saved['sample']['journey_http']).encode())])
    def request(path):
        response = next(responses)
        if isinstance(response, Exception):
            raise response
        return response
    monkeypatch.setattr(ops, 'http', request)
    monkeypatch.setattr(ops.time, 'sleep', lambda seconds: None)
    ops.wait_gateway(saved)
    monkeypatch.setattr(ops, 'http', lambda path: (200, {}, b'{"id":"changed"}'))
    with pytest.raises(ValueError, match='Persisted journey changed'):
        ops.wait_gateway(saved)
