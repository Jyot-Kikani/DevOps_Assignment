from contextlib import asynccontextmanager
import httpx
from stellar_common.api import Settings
from stellar_common.http_client import internal_url

@asynccontextmanager
async def lifespan(app):
    app.state.settings = Settings.load()
    settings = app.state.settings
    app.state.version_info.labels("calculation", settings.source_sha, settings.snapshot_id).set(1)
    base = internal_url("CATALOG_INTERNAL_URL", "http://catalog:8000")
    async with httpx.AsyncClient(base_url=base, timeout=httpx.Timeout(3, connect=1),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            follow_redirects=False, trust_env=False) as client:
        app.state.catalog_client = client
        try:
            yield
        finally:
            del app.state.catalog_client

def readiness(app):
    # No database. Dependency failures affect requests, not this process's readiness.
    return getattr(app.state, "catalog_client", None) is not None, None
