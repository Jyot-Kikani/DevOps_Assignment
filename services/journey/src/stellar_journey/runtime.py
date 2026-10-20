from contextlib import asynccontextmanager
from datetime import datetime, timezone
import os
from urllib.parse import urlsplit
import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from stellar_common.api import Settings
from stellar_common.database import engine_for


@asynccontextmanager
async def lifespan(app):
    settings = Settings.load()
    base = os.environ.get("CATALOG_INTERNAL_URL","http://catalog:8000")
    parsed = urlsplit(base)
    if parsed.scheme not in ("http","https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("","/"):
        raise ValueError("CATALOG_INTERNAL_URL must be an explicit internal base URL")
    app.state.settings = settings
    app.state.engine = engine_for("JOURNEY_DSN","journey_app","stellar_journey")
    app.state.clock = lambda:datetime.now(timezone.utc)
    app.state.version_info.labels("journey",settings.source_sha,settings.snapshot_id).set(1)
    try:
        async with httpx.AsyncClient(base_url=base,timeout=httpx.Timeout(3,connect=1),
                limits=httpx.Limits(max_connections=20,max_keepalive_connections=10),follow_redirects=False,trust_env=False) as client:
            app.state.catalog_client = client
            yield
    finally:
        app.state.engine.dispose()
        del app.state.engine
        if hasattr(app.state,"catalog_client"):
            del app.state.catalog_client


def readiness(app):
    engine = getattr(app.state,"engine",None)
    if engine is None:
        return False,None
    try:
        with engine.connect() as c:
            version = c.execute(text("SELECT version_num FROM journey.alembic_version")).scalar()
            c.execute(text("SELECT 1 FROM journey.journeys LIMIT 1"))
        return version=="journey_0003",None
    except SQLAlchemyError:
        app.state.query_failures.labels("journey").inc()
        return False,None
