# Batch 2 — P04–P07

Implemented and locally verified on 20 October 2026. Scope stops before P08.
Starting `main` was clean, synced and exactly `49b18b5a6fcca597e1e5ed5eca1d13f63985d789`.
The only remote remains the public `Jyot-Kikani/DevOps_Assignment` repository.

## Phase results and source commits

| Phase | Completed behavior | Commit |
|---|---|---|
| P04 | Private PostgreSQL 17 Compose prerequisite; six protected local credentials; isolated databases/roles/default grants; explicit advisory-locked Alembic migrations; pool/connection limits; real upgrade/rollback/denial/restart checks | [ac86940](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/ac869405a30dcb9b30ebbee055a78bd1de11c6b7) |
| P05 | Sealed input/provenance validation; compact normalization and COPY; deterministic ordinals/chunks; transactional readiness/activation; verified reuse/data rollback; concurrent and killed-process atomicity tests; private importer/maintenance CLI | [ea0707a](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/ea0707a) |
| P06 | All Catalog routes; stable indexed search/cursors; profiles/Sun/ordinals/neighbors/positions/map/chunks; lifespan/readiness/meta; normalized metrics and redacted errors/logs; native Chromium gzip verification; full-data HTTP timings | [5cfdfe1](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/5cfdfe1) |
| P07 | Real Journey→Catalog HTTP; total deadline/retry/no-redirect policy; server calculations; immutable anonymous shares; race-safe idempotency; 30-day expiry/7-day grace; batched purge; additive shape constraints; demo-fixture and malformed-DSN guards | [6574d45](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/6574d45) |

Review the exact file inventory/diff in [PR #4](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/4/files).
Development uses `codex/batch2-p04-p07`; delivery uses the normal protected PR
workflow. Main protection was read back: both required checks, up-to-date branch,
admins included, zero mandatory human approvals. No protections were changed.

Hosted P04, P05 and P06 checkpoints both passed quality/security:
[P04](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39441274603),
[P05](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39442909429),
[P06](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39445942736).
The PR checks show the final reviewed head; the final handoff separately records
its protected merge and the resulting main-push run. A historical phase pass is
not substituted for checks on the final head.

## Validation

- **55 unit/contract tests**, **28 PostgreSQL/HTTP integration tests**, **3 frontend tests** passed; no skipped cases in either Python result.
- Contract/schema/TypeScript drift, frontend typecheck, lint and build passed.
- Frozen tool/dependency/action locks, publication exclusions and full-history pinned Gitleaks passed before every phase push.
- The required `ci / quality` now runs PostgreSQL fixture and real service HTTP checks. Its 25 integration cases exclude the three explicit full-data cases, because CI never downloads or publishes the sealed catalog. Both required check names remain unchanged.
- Native pinned Playwright Chromium 156.0.8078.4 decoded the gzip response to **196,608 bytes**, matched SHA-256 `c29e50e54d901a9002716e3637e6121b8c75f08346ddb6f3abeaf29016129b43`, and resolved ordinal 1 to string ID `5853498713190525696`. Its temporary loopback listener was stopped.

Full sealed-data SQL verification: **331,312 rows**, **300,526 within 100 pc**,
**1,151 within 50 ly**, **142 within 25 ly**, **330,881 G magnitudes**, **324,310
color indices**. Every chunk was independently decompressed/rehashed. There are
**37 chunks**, totaling **6,286,694 compressed bytes**; the default intersecting
chunk is **170,138 bytes**, with a **1,333-byte manifest**. The final full-import
worker peak RSS was **363,315,200 bytes** under its **536,870,912-byte** limit.
Repeated imports verify/reuse rows and exact chunks without duplicating them.

Last full-data warm HTTP measurements (20 sequential worker-loopback requests
per endpoint): profile median **5.139 ms**, search **6.975 ms**, neighbors
**113.049 ms**, map **5.846 ms**. The first alias-search query scanned too much
data; its median was about 423 ms before indexed candidate selection. These
measurements do not satisfy the later ten-client/60-second NF05/P22 gate.

The nearest two real rows yield **6.586761272382793 ly** and
**65.86761272382792 Julian years at 0.1c**. A shared record and matching retry
survived a fresh Journey process with Catalog offline. Six simultaneous same-key
creates produced one 201 and five identical 200 responses. Other checks prove
409 conflicts, 410 expiry, 404 grace/purge boundaries, a 1001-row multi-batch purge,
own-DB failure, request-ID propagation and database isolation.

Reproduce using [P04](P04_DATABASES.md), [P05](P05_IMPORT.md),
[P06](P06_CATALOG.md), [P07](P07_JOURNEYS.md). Detailed local logs, JUnit results,
phase reports and measurements stay ignored under `.local/reports/`. The final
baseline is reactivated with `catalog-import` after fixture checks.

## Resolved failures and human actions

The first credential attempt used a sandbox identity. The normal user and sandbox
have different Windows SIDs, and inherited PowerShell module paths also needed
handling. Credential setup now rejects sandbox execution and verifies exact
current-user ACLs. The empty mount directory created by the failed first Docker
start was replaced with a protected file; only the project container was recreated.
Sandbox-created wheel permissions were corrected and builds run as the normal user.
Clean build staging prevents deleted modules surviving from old build directories.

Test corrections made a checksum candidate actually wrong, inspected metric labels
instead of digits in latency values, and declared JSON content type for malformed
JSON. An early full-import check was deliberately interrupted while changing
single-row verification to bounded batches; rollback preserved active data and
all subsequent full gates passed. The browser probe needed UTF-8 subprocess
decoding and its matching pinned Chromium in `.local/playwright`. None of these
failures is left unresolved. The existing FastAPI/Starlette HTTPX deprecation
warning remains nonblocking; frozen dependencies were retained.

**No immediate human login, MFA, account or setup action is required.** Existing
Git Credential Manager authentication was reused privately. No account visibility,
budget, global PATH, execution policy, Docker/WSL installation or unrelated
container was changed.

## Changed areas and remaining boundaries

- `compose.database.yml`, host secret/DB helpers and `.env.example`: database-only operations, persistent volume and role-specific configuration; no host DB port.
- `stellar_common`: optional database/HTTP helpers, sanitized settings/errors, logs and metrics. Service/job wheels remain separate and use the existing hashed third-party environments.
- Catalog/Journey source and packaged migrations: all backend endpoints and persistence rules; regenerated OpenAPI; shared frontend data types retained without building P08 screens.
- Importer source: offline validation/import/report/smoke/retention; no public mutation/import route.
- Integration/unit tests, native browser probe and clean wheel builder: reproducible real database/service checks and explicit full-data evidence.
- Existing CI quality job and phase/handoff documentation: expanded implemented gates, unchanged security policy and protected workflow.

`validation/`, `design/mockups/`, sealed catalog/notice/provenance bytes and their
historical URLs are preserved. ADR 0004 still governs eventual publication. No
new repository, data release, application image publication or public URL exists
from this batch. Credentials, raw data, binary chunks and DB state stay out of Git.

P08 has not started. Full frontend behavior, complete application Compose/images,
gateway exclusions/rate limits, Kubernetes, scheduled retention, signing/GitOps,
Quick Tunnel access, monitoring/backups/recovery and final performance/accessibility
acceptance remain in their specified later phases. A named Docker volume is not a
host backup. This batch establishes backend phase completion, not full PRD acceptance.
