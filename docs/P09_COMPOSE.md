# P09 â€” Local application

Current six-service topology and transition: [service guide](SIX_SERVICES.md),
[ADR 0006](adr/0006-six-application-services.md), [Batch 9](BATCH9_REPORT.md).
Earlier dated validation describes the original two-backend release.

Run in the normal Windows account from this clone (Docker Desktop Linux engine):

```powershell
python tools/run.py dev-up --json
python tools/run.py smoke --target local --json
python tools/run.py dev-up --no-build --json
python tools/run.py compose-check --json
python tools/run.py dev-down --json
```

Open [the local atlas](http://127.0.0.1:8080/explore). `dev-up` verifies/reuses
protected credentials, verifies the preserved P03 archive, builds eight images,
starts PostgreSQL, runs explicit bootstrap/migration/import jobs, then starts
all six APIs and Web and smokes the actual gateway. `--no-build` reuses the
last local images/release metadata. Stop preserves the named volume. Nothing
here creates a cluster, tunnel, public release or remote package.

The Compose project remains `stellar-atlas-db` and preserves its existing
`postgres-data` volume. It can start with an empty volume; roles, databases,
migrations and the sealed import run in dependency order. PostgreSQL and APIs
have no host port. Web binds only `127.0.0.1:8080`. An occupied port is reported;
unrelated containers are not stopped or replaced. Do not run database-only
integration tests concurrently with an application demonstration: those tests
activate fixture snapshots. Restore the baseline with dev-up afterwards.

`compose-check` creates a real immutable share, restarts PostgreSQL and all
three runtime containers, and checks the identical share plus app smoke. It
retains the anonymous test share for ordinary expiry. A named volume is not a
host backup; backup/restore remains P14.

Eight Dockerfiles use digest-pinned Python, Node and Nginx bases and frozen
dependencies. Python packages build as wheels in a build stage; build tools
are absent from runtime stages. API/job users are UID 10001, Web is UID 101.
Only bootstrap receives admin credentials; migrations/import/runtime each get
their designated role. APIs never migrate themselves. Health checks, CPU/memory
limits and a modest restart policy cover the running application.

The main context excludes secrets, `.local`, original CSV/binaries, mockups and
development outputs. Only the importer gets a separate verified dataset context:
sealed gzip archive, snapshot lock, aliases and source/license/provenance notices.
This is a local P11 preparation asset, not a published P15 download; historical
URLs in the immutable P03 lock remain governed by ADR 0004.

Nginx serves SPA deep links and allows only the intended Catalog/Journey routes.
It blocks positions, docs, metrics, administration and import/migration routes;
limits bodies to 4 KiB; applies simple read/share limits; replaces public request
IDs and sets basic browser headers. The limits use the real peer address rather
than trusting visitor-supplied forwarding headers. Future tunnel traffic shares
its peer limit; that later public-path behavior must be reviewed in P16.

Troubleshooting: inspect `docker compose --env-file .local/compose.env -f
compose.yml --profile database ps` and service logs. Detailed build/job attempts
stay in `.local/reports/db-attempts/`. Run `dev-up` again after a source change;
`--no-build` deliberately keeps the existing source identity.

Validation on 21 October 2026: four images built; all running containers healthy;
repeat startup passed; a share survived restarting PostgreSQL/Catalog/Journey/Web
with identical frozen JSON; nine private routes returned 404; both browser flows
passed through Nginx. An isolated empty-volume project imported the full sealed
catalog and passed smoke, then only that temporary project/volume was removed
and the original application restored. Reproduce that explicit isolated check
with `python tools/check_compose_fresh.py` (it temporarily stops the normal app).
Initial Nginx regex quoting and closing-brace errors were fixed before these
passes. Existing 55 Python and 5 frontend tests plus drift/lint/build passed.
