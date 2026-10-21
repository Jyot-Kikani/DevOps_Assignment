"""Existing noninteractive GitHub authentication. Credentials never leave child envs."""
import json
import os
import subprocess

from .bootstrap import ROOT, find_tool

REPOSITORY = 'Jyot-Kikani/DevOps_Assignment'


def environment():
    env = os.environ.copy()
    env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never', GH_PROMPT_DISABLED='1')
    if env.get('GH_TOKEN') or env.get('GITHUB_TOKEN'):
        return env
    gh = find_tool('gh')
    probe = subprocess.run([gh, 'api', 'user', '--jq', '.login'], env=env, cwd=ROOT,
        capture_output=True, timeout=30)
    if probe.returncode == 0:
        return env
    saved = subprocess.run(['git', '-c', 'credential.interactive=false', 'credential', 'fill'],
        input=b'protocol=https\nhost=github.com\n\n', env=env, cwd=ROOT, capture_output=True, timeout=30)
    fields = dict(line.split('=', 1) for line in saved.stdout.decode().splitlines() if '=' in line)
    if saved.returncode or not fields.get('password'):
        raise ValueError('Existing GitHub credential unavailable; human login required')
    env['GH_TOKEN'] = fields['password']
    return env


def call(args, timeout=180):
    result = subprocess.run([find_tool('gh'), *args], cwd=ROOT, env=environment(),
        capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise ValueError('GitHub operation failed: ' + result.stderr[-2000:])
    return result.stdout


def api(path):
    return json.loads(call(['api', path]))
