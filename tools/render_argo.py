"""Render the pinned namespace install; no upstream/vendored bytes are modified."""
import json
import yaml
from stellar_ops.bootstrap import ROOT, digest

lock = json.loads((ROOT / 'tools/toolchain.lock.json').read_text())
path = ROOT / 'infra/vendor/argocd/argocd-namespace-install.yaml'
if digest(path) != lock['vendor']['argocd-namespace-install.yaml']['sha256']:
    raise ValueError('Vendored Argo install checksum mismatch')
documents = list(yaml.safe_load_all(path.read_text()))
items = []
for document in documents:
    if not document:
        continue
    name = document['metadata']['name']
    if any(part in name for part in ('dex-server', 'applicationset-controller', 'notifications-controller')):
        continue
    document['metadata']['namespace'] = 'argocd'
    spec = document.get('spec', {}).get('template', {}).get('spec')
    if spec:
        for container in spec.get('containers', []) + spec.get('initContainers', []):
            tag = container['image']
            entry = lock['images'].get(tag) or lock['images'].get(tag.rsplit('/', 1)[-1])
            if not entry:
                raise ValueError('Argo image is not pinned: ' + tag)
            container['image'] = entry['ref']
    items.append(document)
print(json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': items}))
