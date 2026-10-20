"""One-shot role/database bootstrap; only this job receives admin credentials."""
from pathlib import Path
import psycopg
from psycopg import sql

def secret(name):
    return (Path('/run/secrets') / name).read_text().strip()

def main():
    for database, owner, runtime, schema in [('stellar_catalog', 'catalog_writer', 'catalog_reader', 'catalog'),
            ('stellar_journey', 'journey_owner', 'journey_app', 'journey')]:
        with psycopg.connect(host='postgres', user='postgres', password=secret('postgres_admin'), dbname='postgres', autocommit=True) as connection:
            for role in (owner, runtime):
                if not connection.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
                    connection.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT').format(sql.Identifier(role), sql.Literal(secret(role))))
            if not connection.execute('SELECT 1 FROM pg_database WHERE datname=%s', (database,)).fetchone():
                connection.execute(sql.SQL('CREATE DATABASE {} OWNER {}').format(sql.Identifier(database), sql.Identifier(owner)))
            connection.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(database)))
            connection.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO {}, {}').format(sql.Identifier(database), sql.Identifier(owner), sql.Identifier(runtime)))
        with psycopg.connect(host='postgres', user='postgres', password=secret('postgres_admin'), dbname=database) as connection:
            connection.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
            connection.execute(sql.SQL('CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}').format(sql.Identifier(schema), sql.Identifier(owner)))
            connection.execute(sql.SQL('REVOKE ALL ON SCHEMA {} FROM PUBLIC').format(sql.Identifier(schema)))
            connection.execute(sql.SQL('GRANT USAGE ON SCHEMA {} TO {}').format(sql.Identifier(schema), sql.Identifier(runtime)))
            rights = sql.SQL('SELECT' if schema == 'catalog' else 'SELECT, INSERT, DELETE')
            connection.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} REVOKE ALL ON TABLES FROM PUBLIC').format(sql.Identifier(owner), sql.Identifier(schema)))
            connection.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA {} GRANT {} ON TABLES TO {}').format(sql.Identifier(owner), sql.Identifier(schema), rights, sql.Identifier(runtime)))
            connection.execute(sql.SQL('GRANT {} ON ALL TABLES IN SCHEMA {} TO {}').format(rights, sql.Identifier(schema), sql.Identifier(runtime)))
    print('{"status":"passed","scope":"role/database bootstrap only"}')

if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('{"status":"failed","message":"Database bootstrap failed; credentials not logged"}')
        raise SystemExit(1)
