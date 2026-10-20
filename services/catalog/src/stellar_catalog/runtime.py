from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from stellar_common.api import Settings
from stellar_common.database import engine_for


@asynccontextmanager
async def lifespan(app):
    app.state.settings = Settings.load()
    app.state.engine = engine_for("CATALOG_READER_DSN", "catalog_reader", "stellar_catalog")
    app.state.version_info.labels("catalog",app.state.settings.source_sha,app.state.settings.snapshot_id).set(1)
    try:
        yield
    finally:
        app.state.engine.dispose()
        del app.state.engine


def readiness(app):
    engine = getattr(app.state,"engine",None)
    if engine is None:
        return False,None
    try:
        with engine.connect() as c:
            version = c.execute(text("SELECT version_num FROM catalog.alembic_version")).scalar()
            active_row = c.execute(text("SELECT a.snapshot_id,s.provenance FROM catalog.active_snapshot a JOIN catalog.snapshots s ON s.id=a.snapshot_id WHERE s.status='ready'")).first()
            active = active_row[0] if active_row else None
            required = c.execute(text("SELECT provenance FROM catalog.snapshots WHERE id=:s AND status='ready'"),{"s":app.state.settings.snapshot_id}).scalar()
            safe = required is not None and not (app.state.settings.app_env == "demo" and
                    (required.get("fixture") or (active_row and active_row[1].get("fixture"))))
            return version == "catalog_0002" and active is not None and safe,active
    except SQLAlchemyError:
        app.state.query_failures.labels("catalog").inc()
        return False,None
