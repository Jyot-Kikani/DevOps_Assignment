# P07 Journey calculation, immutable sharing and expiry

Journey uses Catalog's internal positions endpoint over HTTP. It imports no
Catalog package and receives no Catalog database credential. Runtime configuration
uses only its own `JOURNEY_DSN`/file plus a fixed operator-configured
`CATALOG_INTERNAL_URL`. HTTPX is lifespan-managed, disables redirects/environment
proxies, uses a one-second connect timeout and a three-second total deadline
covering both attempts. Connection/reset/503 failures get at most one retry.
Requests propagate the validated request ID; returned snapshot/object IDs and
finite positions are validated before calculations.

`POST /v1/estimate` accepts only snapshot, origin/destination string IDs and speed.
The server calculates float64 Euclidean separation and constant-speed travel
using the shared frozen constants/model. Client coordinates, distance, duration
or remote URL fields are rejected. Assumptions explicitly exclude acceleration,
gravity and relativity.

`POST /v1/journeys` requires a UUID `Idempotency-Key`. It normalizes/hashes inputs,
recalculates through Catalog, and inserts a server-generated UUID with frozen
positions/results and UTC creation/expiry timestamps. PostgreSQL's unique key
and `ON CONFLICT DO NOTHING` arbitrate races in a transaction. One create returns
201; matching retries return 200 and the same immutable body/Location. Different
inputs with the same key return 409. A retained matching retry can return its
frozen body even when Catalog is offline. Expired retries do not create a new link.

`GET /v1/journeys/{uuid}` returns frozen data for 30 days, 410 for the next seven
days, then 404. The idempotency key/hash and visitor identity are never returned.
The schema contains no IP, email, cookie, user title or account fields. Shared
UUIDs are public links; browser share URLs use the current origin in P08.

Private maintenance `python -m stellar_importer retention --json` uses only the
Journey app role and deletes records past expiry+7 days in batches of 1000 using
the expiry index. Daily scheduling at `0 3 * * *` UTC belongs to the Kubernetes
CronJob wiring in P13; no scheduler or cluster is claimed by P07. Database triggers
deny updates and deletion before retention elapses. The additive `journey_0003`
revision also rejects empty position arrays, infinite timestamps and non-array
assumptions without rewriting the frozen v1 migration. Run `db-bootstrap` after
rebuilding wheels to upgrade explicitly.

Journey's liveness checks the process; readiness checks its own DB/migration head.
Catalog outage produces 503 calculations while existing shared reads and Journey
readiness continue. Health/meta/normalized metrics/error envelopes/JSON logging
use the same common boundary as Catalog. API processes never migrate at startup.

Validation:

```powershell
python tools/build_packages.py
python tools/run.py db-bootstrap --json
python tools/run.py contracts --check --json
python tools/run.py test --json
python tools/run.py db-check --full --json
```

Real PostgreSQL/HTTP tests cover the 3-4-5 oracle, Sun/Proxima, bounds, unknown
objects, request-ID propagation, six-way idempotency races, frozen old snapshots,
409 conflicts, controlled-clock 410/404 boundaries, 1001-row multi-batch purge,
database constraints, timeout/retry/redirect/mismatched-snapshot behavior and own
database failure. The explicit full-data gate verifies the two nearest real
catalog rows: approximately 6.5867612724 ly and 65.867612724 Julian years at 0.1c.
It restarts Journey with Catalog offline and verifies the same stored share and
matching idempotent retry. Details are in `.local/reports/p07-full-http.json`.

This is backend verification. P08 screens, public share UI, P09 complete container
startup, later gateway exclusions and Kubernetes scheduling remain unimplemented.
