"""Linux maintenance entry point. Credentials stay in files/process memory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from stellar_common.database import migrate

ROOT = Path(__file__).resolve().parents[1]
ROLES = {"stellar_catalog": ("catalog_writer", "catalog_reader", "catalog"),
         "stellar_journey": ("journey_owner", "journey_app", "journey")}


def url(role, database):
    password = (ROOT / ".local/secrets" / role).read_text().strip()
    return URL.create("postgresql+psycopg", username="postgres" if role == "postgres_admin" else role,
                      password=password, host="postgres", database=database)


def configure():
    names = {"CATALOG_WRITER_DSN": ("catalog_writer", "stellar_catalog"), "CATALOG_READER_DSN": ("catalog_reader", "stellar_catalog"),
             "JOURNEY_OWNER_DSN": ("journey_owner", "stellar_journey"), "JOURNEY_DSN": ("journey_app", "stellar_journey")}
    for name, (role, database) in names.items():
        os.environ[name] = url(role, database).render_as_string(hide_password=False)
    os.environ.setdefault("APP_ENV", "ci")


def bootstrap():
    import psycopg
    from psycopg import sql
    admin = create_engine(url("postgres_admin", "postgres"), isolation_level="AUTOCOMMIT", hide_parameters=True)
    with admin.connect() as c:
        for database, (owner, runtime, schema) in ROLES.items():
            for role in (owner, runtime):
                if not c.execute(text("SELECT 1 FROM pg_roles WHERE rolname=:r"), {"r": role}).scalar():
                    # SQL identifiers/literals are composed with psycopg quoting; never logged.
                    password = (ROOT / ".local/secrets" / role).read_text().strip()
                    statement = sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(sql.Identifier(role), sql.Literal(password))
                    c.connection.driver_connection.execute(statement)
            if not c.execute(text("SELECT 1 FROM pg_database WHERE datname=:d"), {"d": database}).scalar():
                c.exec_driver_sql(f"CREATE DATABASE {database} OWNER {owner}")
            c.exec_driver_sql(f"REVOKE ALL ON DATABASE {database} FROM PUBLIC")
            c.exec_driver_sql(f"GRANT CONNECT ON DATABASE {database} TO {owner}, {runtime}")
    admin.dispose()
    for database, (owner, runtime, schema) in ROLES.items():
        admin = create_engine(url("postgres_admin", database), hide_parameters=True)
        with admin.begin() as c:
            c.exec_driver_sql("REVOKE ALL ON SCHEMA public FROM PUBLIC")
            c.exec_driver_sql(f"CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {owner}")
            c.exec_driver_sql(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
            c.exec_driver_sql(f"GRANT USAGE ON SCHEMA {schema} TO {runtime}")
            rights = "SELECT" if schema == "catalog" else "SELECT, INSERT, DELETE"
            c.exec_driver_sql(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} REVOKE ALL ON TABLES FROM PUBLIC")
            c.exec_driver_sql(f"ALTER DEFAULT PRIVILEGES FOR ROLE {owner} IN SCHEMA {schema} GRANT {rights} ON TABLES TO {runtime}")
            c.exec_driver_sql(f"GRANT {rights} ON ALL TABLES IN SCHEMA {schema} TO {runtime}")
        admin.dispose()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--phase")
    args = parser.parse_args()
    configure()
    if args.action == "db-bootstrap":
        bootstrap()
        for schema, role, database in (("catalog", "catalog_writer", "stellar_catalog"), ("journey", "journey_owner", "stellar_journey")):
            engine = create_engine(url(role, database), hide_parameters=True)
            migrate("stellar_" + schema, schema, engine)
            engine.dispose()
        print(json.dumps({"status": "passed", "databases": list(ROLES), "migrations": "head"}))
    elif args.action == "db-check":
        os.environ["STELLAR_DB_TESTS"] = "1"
        cases = {"P04": "tests/integration/test_database.py", "P05": "tests/integration/test_import.py",
                 "P06": "tests/integration/test_catalog.py", "P07": "tests/integration/test_journey.py"}
        command = [sys.executable, "-m", "pytest", cases.get(args.phase, "tests/integration"), "-q", "-rA",
                   "--basetemp=/tmp/stellar-pytest", "-o", "cache_dir=/tmp/stellar-cache",
                   "--junitxml=.local/reports/batch2-integration.xml"]
        if args.full:
            os.environ["STELLAR_FULL_DATA"] = "1"
            if args.phase == "P05":
                command.append("tests/integration/test_full_data.py")
        raise SystemExit(subprocess.call(command))
    else:
        from stellar_importer.pipeline import load_catalog, report
        if args.action == "catalog-import":
            result = load_catalog(ROOT / "validation/gcns_required_fields.csv", ROOT / "data/snapshot.lock.json",
                                  archive=ROOT / ".local/data/sealed/gcns-edr3-20261013-20271720/gcns-required-fields.csv.gz",
                                  aliases_path=ROOT / "data/aliases.csv", activate=True)
        else:
            result = report()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "message": "Maintenance failed; no credentials logged"}))
        raise SystemExit(1)
