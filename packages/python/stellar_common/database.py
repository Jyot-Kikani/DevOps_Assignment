"""Optional SQLAlchemy helpers; callers install their locked database dependencies."""
from pathlib import Path
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def secret_value(name):
    file = os.environ.get(name + "_FILE")
    return Path(file).read_text().strip() if file else os.environ.get(name)


def engine_for(name, role, database):
    value = secret_value(name)
    if not value:
        raise ValueError(f"Configure {name} or {name}_FILE")
    try:
        url = make_url(value)
    except Exception:
        raise ValueError(f"{name} is not a valid database URL") from None
    if url.drivername != "postgresql+psycopg" or url.username != role or url.database != database:
        raise ValueError(f"{name} must use its designated PostgreSQL role and database")
    timeout = 600000 if role in ("catalog_writer", "journey_owner") else 5000
    return create_engine(url, pool_size=5, max_overflow=2, pool_timeout=3, pool_pre_ping=True,
                         hide_parameters=True, connect_args={"connect_timeout": 3,
                         "options": f"-c statement_timeout={timeout} -c lock_timeout=30000 -c timezone=UTC"})


def migrate(package, schema, engine, revision="head"):
    """One connection/transaction and advisory lock cover the whole Alembic upgrade."""
    from importlib.resources import files
    from alembic import command
    from alembic.config import Config
    config = Config()
    config.set_main_option("script_location", str(files(package) / "migrations"))
    with engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": schema + "-migration"})
        config.attributes.update(connection=connection, schema=schema)
        command.upgrade(config, revision)
        if schema == "journey":
            # Default DML grants apply to future app tables, but migration history
            # is owned by the migration role and must stay read-only at runtime.
            connection.exec_driver_sql("REVOKE INSERT, UPDATE, DELETE ON journey.alembic_version FROM journey_app")


def alembic_environment():
    from alembic import context
    connection = context.config.attributes["connection"]
    context.configure(connection=connection, version_table_schema=context.config.attributes["schema"],
                      transactional_ddl=True)
    with context.begin_transaction():
        context.run_migrations()
