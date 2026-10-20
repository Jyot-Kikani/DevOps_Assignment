# P04 databases, credentials and migrations

PostgreSQL 17 runs in the `database` profile of `compose.database.yml`, pinned
to the P00 digest. It has a named volume, max_connections 60, UTC timestamps,
and no published host port. This is the database prerequisite only; complete
application Compose startup belongs to P09.

Run in the normal Windows account, after the documented locked environment setup:

```powershell
python tools/build_packages.py
python tools/run.py secrets-init --json
python tools/run.py db-start --json
python tools/run.py db-bootstrap --json
python tools/run.py db-check --phase P04 --json
python tools/run.py db-stop --json
```

`secrets-init` generates/reuses six independent credentials in ignored
`.local/secrets`. It verifies current-user-only DACLs on Windows (0700/0600 on
Linux), rejects sandbox identities, symlinks and non-file credential paths,
and prints no values. Run it as the operator; a sandbox account must not become
the owner of operator credentials. Do not copy these files into Git or evidence.

Maintenance runs in a disposable pinned Linux Python container on the private
database network. Its cached environment is installed from the existing hashed
Linux locks; first-party wheels are rebuilt explicitly before changes are tested.
Only this maintenance process receives admin credentials. Runtime APIs use one
role-specific DSN or `*_DSN_FILE`, validated against their own database and role.
The pool is 5 connections plus at most 2 overflow connections.

Bootstrap creates `stellar_catalog`/`stellar_journey`, owners
`catalog_writer`/`journey_owner`, runtime roles `catalog_reader`/`journey_app`,
revokes public database/schema access, and applies matching default privileges.
It reuses existing roles/passwords and databases. It does not rotate credentials.
Catalog runtime has SELECT only. Journey runtime has SELECT/INSERT/DELETE only;
triggers prevent updates and premature deletion of shared records.

Each service has a packaged Alembic revision chain: v1 tables then additive
indexes/guards. Migration upgrades hold a transaction-level advisory lock and
never run on API startup. Repeated head upgrades do nothing. Downgrades fail.
Ready catalog snapshots and their rows/aliases/chunks are immutable; the active
pointer accepts ready snapshots only. Journey rows retain frozen positions and
calculations. PostgreSQL enforces bounds, finite numbers, IDs and timestamps.

The integration suite uses real PostgreSQL, including scratch databases for
fresh/previous-revision upgrades, a sentinel row preserved across upgrades,
failed-DDL rollback, repeat head upgrades, reader write/DDL denial and all four
cross-database denials. Missing PostgreSQL is a test failure. CI runs this suite
inside the existing required `ci / quality` job. Detailed outputs stay in
`.local/reports/db-check-worker.log` and `batch2-integration.xml`.

Stopping/restarting the project container retains the named volume. This is
local persistence, not a host backup or Kubernetes recovery demonstration.
