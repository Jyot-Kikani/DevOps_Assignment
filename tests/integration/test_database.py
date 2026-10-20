import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from stellar_common.database import engine_for, migrate


def test_migrations_repeat_and_real_postgres():
    for package, schema, variable, role, database in (
        ("stellar_catalog", "catalog", "CATALOG_WRITER_DSN", "catalog_writer", "stellar_catalog"),
        ("stellar_journey", "journey", "JOURNEY_OWNER_DSN", "journey_owner", "stellar_journey")):
        engine = engine_for(variable, role, database)
        migrate(package, schema, engine)
        migrate(package, schema, engine)
        with engine.connect() as c:
            assert c.execute(text("SHOW server_version_num")).scalar().startswith("17")
            head = "catalog_0002" if schema == "catalog" else "journey_0003"
            assert c.execute(text(f"SELECT version_num FROM {schema}.alembic_version")).scalar() == head
        with pytest.raises(Exception):
            migrate(package, schema, engine, "nonexistent_revision")
        with engine.connect() as c:
            assert c.execute(text(f"SELECT version_num FROM {schema}.alembic_version")).scalar() == head
        assert engine.pool.size() == 5 and engine.pool._max_overflow == 2
        engine.dispose()


def test_reader_and_cross_database_denials():
    reader = create_engine(os.environ["CATALOG_READER_DSN"], hide_parameters=True)
    with reader.connect() as c:
        assert c.execute(text("SELECT count(*) FROM catalog.snapshots")).scalar() >= 0
    for sql in ("CREATE TABLE catalog.forbidden(id int)", "CREATE TABLE public.forbidden(id int)",
                "INSERT INTO catalog.active_snapshot VALUES(true,'forbidden')"):
        with pytest.raises(DBAPIError):
            with reader.begin() as c:
                c.execute(text(sql))
    for variable, other in (("CATALOG_READER_DSN", "stellar_journey"), ("CATALOG_WRITER_DSN", "stellar_journey"),
                             ("JOURNEY_DSN", "stellar_catalog"), ("JOURNEY_OWNER_DSN", "stellar_catalog")):
        from sqlalchemy.engine import make_url
        engine = create_engine(make_url(os.environ[variable]).set(database=other), hide_parameters=True)
        with pytest.raises(DBAPIError):
            with engine.connect():
                pass
        engine.dispose()
    reader.dispose()


def test_constraints_and_transaction_rollback():
    engine = create_engine(os.environ["CATALOG_WRITER_DSN"], hide_parameters=True)
    with engine.connect() as c:
        before = c.execute(text("SELECT count(*) FROM catalog.snapshots")).scalar()
    with pytest.raises(DBAPIError):
        with engine.begin() as c:
            c.execute(text("INSERT INTO catalog.active_snapshot VALUES(true,'not-ready')"))
    with engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM catalog.snapshots")).scalar() == before
    engine.dispose()


def test_fresh_previous_revision_upgrade_and_failed_ddl_preserve_rows(tmp_path):
    from uuid import uuid4
    from sqlalchemy.engine import make_url
    # Disposable scratch databases only. Existing application databases stay intact.
    admin_url = make_url(os.environ["CATALOG_WRITER_DSN"]).set(username="postgres", database="postgres",
        password=__import__("pathlib").Path(".local/secrets/postgres_admin").read_text().strip())
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT", hide_parameters=True)
    for package, schema, owner in (("stellar_catalog", "catalog", "catalog_writer"), ("stellar_journey", "journey", "journey_owner")):
        name = "stellar_check_" + uuid4().hex
        with admin.connect() as c:
            c.exec_driver_sql(f"CREATE DATABASE {name} OWNER {owner}")
        variable = "CATALOG_WRITER_DSN" if schema == "catalog" else "JOURNEY_OWNER_DSN"
        engine = create_engine(make_url(os.environ[variable]).set(database=name), hide_parameters=True)
        try:
            with engine.begin() as c:
                c.exec_driver_sql(f"CREATE SCHEMA {schema} AUTHORIZATION {owner}")
            migrate(package, schema, engine, schema + "_0001")
            with engine.begin() as c:
                c.exec_driver_sql(f"CREATE TABLE {schema}.upgrade_sentinel (id int PRIMARY KEY)")
                c.exec_driver_sql(f"INSERT INTO {schema}.upgrade_sentinel VALUES (7)")
            migrate(package, schema, engine)
            migrate(package, schema, engine)
            head = "catalog_0002" if schema == "catalog" else "journey_0003"
            from importlib.resources import files
            import shutil
            from alembic import command
            from alembic.config import Config
            scripts = tmp_path / schema
            shutil.copytree(str(files(package) / "migrations"), scripts)
            (scripts / "versions/0003_bad.py").write_text(
                "from alembic import op\nrevision='bad_9999'\ndown_revision='" + head + "'\n"
                "def upgrade():\n    op.execute('ALTER TABLE " + schema + ".upgrade_sentinel ADD COLUMN incomplete text')\n"
                "    op.execute('SELECT missing_migration_function()')\n")
            config = Config()
            config.set_main_option("script_location", str(scripts))
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.exec_driver_sql("SELECT pg_advisory_xact_lock(hashtext('migration-test'))")
                    config.attributes.update(connection=c, schema=schema)
                    command.upgrade(config, "head")
            with engine.connect() as c:
                assert c.exec_driver_sql(f"SELECT id FROM {schema}.upgrade_sentinel").scalar() == 7
                assert c.exec_driver_sql(f"SELECT version_num FROM {schema}.alembic_version").scalar() == head
                assert c.execute(text("SELECT count(*) FROM information_schema.columns WHERE table_schema=:s AND table_name='upgrade_sentinel' AND column_name='incomplete'"), {"s": schema}).scalar() == 0
        finally:
            engine.dispose()
            with admin.connect() as c:
                c.exec_driver_sql(f"DROP DATABASE {name}")
    admin.dispose()
