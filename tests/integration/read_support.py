from contextlib import ExitStack
import re
from fastapi.testclient import TestClient
from stellar_catalog.app import app as catalog
from stellar_search.app import app as search
from stellar_atlas_map.app import app as atlas_map
from stellar_snapshot.app import app as snapshot

APPS = dict(catalog=catalog, search=search, atlas_map=atlas_map, snapshot=snapshot)

def owner(path):
    path = path.split('?')[0]
    if re.search(r'/stars$|/neighbors$', path): return 'search'
    if re.search(r'/map$|/chunks/', path): return 'atlas_map'
    if re.fullmatch(r'/v1/snapshots/[^/]+', path): return 'snapshot'
    return 'catalog'

class ReadClient:
    def __enter__(self):
        self.stack = ExitStack()
        self.clients = {name:self.stack.enter_context(TestClient(app)) for name,app in APPS.items()}
        return self
    def __exit__(self, *args): return self.stack.__exit__(*args)
    def get(self, path, **kwargs): return self.clients[owner(path)].get(path, **kwargs)
    def post(self, path, **kwargs): return self.clients[owner(path)].post(path, **kwargs)


class LiveReadClient:
    """Dispatch to four real HTTP processes for the optional full-data gate."""
    def __init__(self, sid, tmp_path):
        self.sid, self.tmp_path = sid, tmp_path
    def __enter__(self):
        import httpx
        from http_support import live_service
        self.stack = ExitStack()
        self.bases = {role:self.stack.enter_context(live_service(role,self.sid,self.tmp_path))[0] for role in APPS}
        self.client = self.stack.enter_context(httpx.Client(timeout=10,trust_env=False))
        return self
    def __exit__(self, *args): return self.stack.__exit__(*args)
    def get(self, path, **kwargs): return self.client.get(self.bases[owner(path)] + path, **kwargs)
