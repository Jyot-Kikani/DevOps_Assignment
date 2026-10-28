# Stellar Atlas — Detailed Implementation and Delivery Plan

Version: 1.4 | Course-scope revision: 20 October 2026 | Frozen design date: 18 October 2026 | Public repository/protected-main revision: 20 October 2026 | Companion: [PRD.md](PRD.md)

The user selected Cloudflare Quick Tunnel as the primary public-access method on 19 October 2026. [ADR 0001](adr/0001-public-access-quick-tunnel.md) supersedes the original Tailscale-first choice. On 20 October the user selected the existing `Jyot-Kikani/DevOps_Assignment` repository exclusively and authorized basic GitHub CI before Batch 2; [ADR 0004](adr/0004-existing-repository-and-early-ci.md) records this change. The user then made this repository public. Public visibility and free main protection are live-verified. No new `stellar-atlas` repository is to be created. The course-scope amendment in [ADR 0005](adr/0005-course-assignment-scope.md) now controls future work and supersedes the earlier production-hardening requirements.

The user approved a post-completion [six-service refactor](adr/0006-six-application-services.md).
Its topology supersedes the original two-backend design without changing product
features or scientific rules. See [Batch 9](BATCH9_REPORT.md) for actual status.

## 0. Execution rules, scope, and evidence boundary

This is an end-to-end implementation specification, not an instruction to invent a second architecture. Implement phases P00–P23 in order. Complete each phase's revised course checks before its dependants. Keep the existing P00–P07 implementation and checks; do not expand them without a concrete defect or course requirement. Every product requirement has an implementation phase and final evidence check below.

The plan covers account/bootstrap setup, data, contracts, services, UI, containers, local infrastructure, security, CI/CD, public access, monitoring, recovery, performance, assessment, and handoff. Advanced items explicitly marked optional are outside the required course submission; their absence is not a failed acceptance result.

Some values necessarily come from execution: authenticated GitHub owner, available host resources, generated passwords, resolved image digests, and assigned tunnel hostname. The acquisition rule for each is fixed here. They are inputs/results, not open architecture decisions. Do not invent account identities or successful measurements. If a prerequisite is unavailable, record that precise blocker and complete independent work; do not buy a replacement service or silently weaken a security gate.

Writing this plan does not initialize Git, install software, create accounts, publish repositories, or deploy anything. A later implementing agent executes it only when asked to implement. Login, MFA, and account ownership remain with the human. Routine coding and reversible verification do not need new design approval. Destructive operations must target only the explicitly named project resources and follow the backup/path checks below.

### 0.0 Course-sized work and checks (controlling amendment)

This is a university assignment. Implement the smallest clear, reliable demonstration
of each selected course topic. Preserve the working product, scientific data,
zero-cost/local-host constraints and protected Git workflow. P00–P07 are complete;
this revision changes future expectations, not their historical evidence.

- Reuse existing tests. Add a normal-path check and a representative failure only
  where new behavior warrants it; do not build exhaustive permutations or pursue
  coverage percentages. Manual screenshots/commands are valid course evidence.
- Run focused checks while changing code, then the existing required CI once per
  reviewable milestone. Repeat full-data/browser checks only after a relevant
  importer, binary, calculation or integration change, or once at final acceptance.
- Keep ordinary validation, secret exclusion, private DB/admin access, basic role
  isolation, healthy startup, persistent storage and a real backup/restore.
- Signing/SBOM infrastructure, custom CNI/default-deny policy matrices, disposable
  CI clusters, scanner exception/age frameworks, chaos/stale-release race tests,
  automated disaster recovery and strict load/FPS SLOs are optional extensions.
- Do not install optional tools or implement optional commands just because they
  remain in the frozen lock, old schema, a previous report or an example tree.
  Update a future-facing contract explicitly when simplifying it; never fill
  obsolete signature/SBOM fields with invented values.
- No faculty rubric/handout is present in this repository. Do not call the old
  plan's extra gates faculty requirements. If supplied course material explicitly
  requires an optional item, implement that item at demonstration scale.

### 0.1 Verified starting state

- Workspace: `C:\Users\jyoth\OneDrive\Desktop\Jyot\Coding\VSCode\Sem_7\DevOps Assignment`.
- Existing directories: `validation/`, `design/mockups/`, and these planning documents.
- No application source or Git repository was present during planning.
- Existing selected-field CSV rehashed successfully: 50,104,120 bytes; SHA-256 `20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94`.
- Historical validation measured 331,312 records, all with finite Cartesian coordinates and distances. See `validation/catalog_validation.json`.
- Installed command probes found Git, Python 3.13.5, Node 22.16.0, Docker CLI 29.7.2, kubectl, and WSL. kind and Terraform were not on PATH.
- Docker server connection, WSL enumeration, and hardware queries were not verified: the planning sandbox reported missing daemon/access-denied errors. These are prerequisite checks to repeat in the user's normal session, not evidence of a broken installation.
- No browser-performance, cluster, workflow, account-plan, or live-public-link claim has been verified.

### 0.2 Frozen architectural decisions

| Decision | Required implementation |
|---|---|
| Budget | Existing local hardware; no paid services, domains, cloud resources, or expiring credits. |
| Host | Windows with Docker Desktop Linux containers/WSL2; PowerShell orchestration. Containers and CI use Linux. |
| Runtime budget | Reference host at least 16 GiB RAM, 4 logical CPUs and 40 GiB free disk; Docker allocation target 8 GiB RAM/4 CPUs. Measure before installation. If insufficient, use another existing team machine and the same architecture; do not purchase compute. |
| Repository | Use only the existing public `Jyot-Kikani/DevOps_Assignment`, source branch `main`, deployment branch `deploy`. Preserve contents/history and `origin`; never force-push. Main requires up-to-date PRs and passing `ci / quality` and `ci / security`, including admins; no mandatory second-person approval. Application name, Kubernetes namespace and image prefixes remain `stellar-atlas`. |
| Frontend | React + TypeScript + Vite; direct Three.js renderer managed through React lifecycle; plain CSS; system fonts. No React Three Fiber, state framework, paid UI library, or external font dependency. |
| APIs | Two independently packaged FastAPI services: Catalog and Journey. SQLAlchemy + psycopg, Alembic migrations, HTTPX for the Journey-to-Catalog call. One Uvicorn process per container. |
| Data | Immutable baseline snapshot; normalized PostgreSQL rows and pre-generated gzip binary map chunks. No runtime astronomy API calls. |
| Persistence | One PostgreSQL 17 instance; separate catalog/journey databases and credentials. Catalog API is read-only. No service queries the other database. |
| Saved items | Browser localStorage only. Shared journeys are immutable, anonymous, expiring server records. No accounts. |
| Local development | Docker Compose with frontend gateway, both APIs, PostgreSQL, and one-shot migrations/import. |
| Kubernetes | One-node kind cluster `stellar-atlas-demo`, default kind networking and local-path PVCs. Calico/network-policy demonstrations are optional. No host-level HA claim. |
| Public routing | Web container is also the reverse proxy. NodePort 30080 maps to host `127.0.0.1:8080`. No additional ingress controller or cloud load balancer. |
| IaC ownership | kind owns the cluster; Terraform owns the small local platform (namespaces, storage, PostgreSQL, basic monitoring); Argo owns application resources. Add policies/quotas only when needed. |
| Application delivery | GitHub Actions builds/scans/publishes images, writes approved digest manifests to `deploy`; local Argo CD pulls that branch. No long-lived self-hosted GitHub runner or inbound cluster credentials. |
| Security tools | Keep existing Gitleaks; use one Grype image scan for the DevSecOps demo. Additional SAST/dependency/IaC scanners and signing/SBOM tools are optional unless the course explicitly requires them. |
| Monitoring | Plain manifests for Prometheus, Grafana, and kube-state-metrics; no Helm/operator dependency. Metrics are local-only. Structured application logs go to stdout. |
| Public tunnel | Accountless Cloudflare Quick Tunnel to the local Kubernetes gateway. No purchased domain. Record the actual temporary URL after each start; no stable-hostname promise. |
| Rollback | Restore previous application manifests through a new commit on `deploy`. Never rely on `kubectl rollout undo` while Argo self-heal is enabled. |
| Database changes | Expand-only/backward-compatible within this release. No automatic schema downgrades or destructive migrations. |

### 0.3 Tool and version policy

These releases were queried from their official release/package metadata during planning; their existence was checked, not their joint runtime compatibility. P00 froze downloaded checksums. P12 validates the tools actually selected for the course demo; unused pins do not require installation or integration checks.

| Tool/library | Baseline |
|---|---|
| Node | 24.22.0 LTS, portable project-local installation; existing Node 22 is not the canonical toolchain |
| Python | 3.13 runtime line; host orchestration supports existing 3.13.5 |
| kind | 0.33.0 |
| Kubernetes/kubectl | 1.35.8 |
| kind node | `kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0` |
| Calico (optional) | Existing pin: 3.33.0; not needed for default kind networking |
| Terraform | 1.16.6; Kubernetes provider compatibility band `~> 3.2` |
| Argo CD | 3.5.5, namespace-scoped non-HA installation plus separately installed CRDs |
| React / React DOM | 19.3.1, matching versions |
| Vite / Vitest / Three.js | 8.3.4 / 5.0.5 / 0.186.1 |
| Playwright | 1.64.1, matching bundled Chromium |
| FastAPI / SQLAlchemy / Alembic / psycopg | 0.146.0 / 2.1.5 / 1.20.0 / 3.3.6 |
| PostgreSQL | Official 17 Bookworm image, exact digest frozen before the first build |
| Prometheus / Grafana / kube-state-metrics | 3.15.0 / 13.2.4 / 2.20.0 |
| Gitleaks / Grype | 8.30.1 / 0.120.1 |
| Cosign / Checkov (optional) | Existing pins: 3.1.3 / 3.3.29; no setup required by default |
| cloudflared | 2026.10.1, portable project-local Windows binary; exact upstream checksums and Linux counterpart frozen in the toolchain lock |

P00 must create `tools/toolchain.lock.json` with exact tool versions, download URLs, SHA-256s, action commit SHAs and runtime image digests. Resolve remaining leaf packages (TypeScript, React types, HTTPX, Uvicorn, pytest, Ruff, Bandit, pip-audit, Syft and metrics client) once from official registries using the highest stable version compatible with these baselines. Save direct versions exactly and commit `package-lock.json`, hashed Python requirements, and `.terraform.lock.hcl`. This is the defined resolution algorithm, not permission to defer tool selection. Commit the resolved results before feature work.

Never use `latest` or a moving tag in deployed manifests. Resolve `python:3.13-slim-bookworm`, `postgres:17-bookworm`, and the Nginx unprivileged Bookworm image into digests once; use only the resulting references. All production dependencies and CI actions are pinned. Release-image security failure is resolved by patched dependencies/base digests within these chosen runtime lines, with lockfile updates and rerun checks. A major-version change requires an ADR explaining the incompatibility and equivalent acceptance tests; it must not silently change the architecture.

## 1. Repository and command contracts

### 1.1 Final layout

```text
stellar-atlas/
  README.md, LICENSE, SECURITY.md, CONTRIBUTING.md, .gitignore, .dockerignore
  ops.ps1                         # complete host command entry point
  .env.example                    # names and harmless defaults only
  .github/workflows/ci.yml, release.yml, rollback.yml, cleanup-artifacts.yml
  .github/dependabot.yml, CODEOWNERS, pull_request_template.md
  apps/web/{src,public,tests,Dockerfile,nginx.conf,package.json,package-lock.json}
  services/catalog/{src,tests,migrations,alembic.ini,Dockerfile,requirements*.txt}
  services/journey/{src,tests,migrations,alembic.ini,Dockerfile,requirements*.txt}
  jobs/catalog-importer/{src,tests,Dockerfile,requirements*.txt}
  packages/python/stellar_common/{ids,units,errors,logging}.py
  contracts/{catalog.openapi.json,journey.openapi.json,map-format.md,release.schema.json}
  data/{snapshot.lock.json,aliases.csv,aliases.sources.json,LICENSE-NOTICE.md}
  tests/{fixtures,integration,e2e,security,performance,restore}
  infra/kind/{cluster.yaml,calico-patch.yaml}
  infra/terraform/{versions.tf,providers.tf,namespaces.tf,rbac.tf,network.tf,
                   storage.tf,database.tf,monitoring.tf,outputs.tf,.terraform.lock.hcl}
  infra/vendor/{calico,argocd}/     # exact downloaded manifests + checksums/licenses
  deploy/templates/{base,demo}/    # source-controlled application manifests
  monitoring/{prometheus.yml,grafana-datasources.yml,dashboards,alerts.yml}
  security/{policy.yml,exceptions.yml,.gitleaks.toml,checkov.yaml}
  tools/{toolchain.lock.json,requirements-ops.txt,stellar_ops/}
  docs/{PRD.md,IMPLEMENTATION_PLAN.md,ARCHITECTURE.md,RUNBOOK.md,
        ACCEPTANCE.md,EVIDENCE_MATRIX.md,DEMO_SCRIPT.md,DATA_PROVENANCE.md,adr/}
  design/mockups/                 # preserve supplied images/prompts
  validation/                     # preserve supplied probes/reports; ignore raw binaries
  .local/                         # ignored tools, secrets, state, datasets, backups, reports
```

The tree is an illustrative inventory, not a requirement to implement optional workflows, policy files or automation.

No virtualenvs, raw catalogs, generated binary chunks, database files, Terraform state, credentials, screenshots of private account information, or browser traces enter Git. Small attributed test fixtures and sanitized evidence summaries do.

### 1.2 Host command API

Implement `ops.ps1` as a strict dispatcher to `python tools/run.py <action>` using argument arrays, explicit paths, checked exit codes, and bounded timeouts. `tools/run.py` imports the stdlib-only `stellar_ops` package from its own tools directory. Never use string-built shell commands or `Invoke-Expression`. Resolve repository root from the script path, not the current terminal directory. Reject unexpected Kubernetes contexts before writes. All destructive filesystem targets must resolve underneath `.local/` and pass an explicit path-containment check.

This inventory includes original optional extensions. Implement only the commands needed by the revised phase checks; existing commands retain their documented behavior.

| Action | Effect when implemented |
|---|---|
| `doctor` | Read-only prerequisites, ports, versions, Docker resources, Linux containers, Git identity; JSON report; nonzero on unsatisfied requirements. |
| `tools-lock` | Download/verify approved tools to `.local/tools`, resolve/pin dependencies/digests/actions, write committed lock artifacts. No global PATH editing. |
| `secrets-init` | Generate local DB/Grafana credentials, apply user-only filesystem access, never print values. |
| `data-seal` | Verify baseline, normalize/validate, produce deterministic gzip archive and provenance/checksum files. |
| `data-publish` | Publish only verified public snapshot asset and notices to the exact data release. |
| `data-activate` | Run the pinned importer Job with `--activate` for an existing ready snapshot or a sealed candidate; validate first and atomically change the active pointer. |
| `dev-up` / `dev-down` | Start healthy Compose environment / stop project containers without deleting volumes. |
| `test` | Run the required unit, integration, contract and frontend tests; reports under `.local/reports`. |
| `security` | Run required security gates and produce normalized results; no silent skip. |
| `images-build` | Build four application images once, with source/dataset labels and pinned bases. |
| `cluster-create` | Create the named kind cluster with default networking; wait for node readiness. |
| `platform-plan` / `platform-apply` | Terraform initialize/validate/plan/apply using ignored local state and the explicit project context. |
| `cluster-secrets` | Apply generated credentials outside Terraform/Argo ownership, redacting input/output. |
| `demo-bootstrap` | Load locally built images and apply local overlay; migrate/import; complete cluster smoke tests. |
| `monitoring-up` | Apply/provision Terraform-owned monitoring and verify scrape targets/dashboards. |
| `gitops-bootstrap` | Install pinned Argo CRDs/namespaced components, restricted RoleBindings, AppProject, Application; enable only when deploy ref is valid. |
| `public-start` / `public-stop` | Enable/disable only this project's tunnel to port 8080; record URL/status and verify HTTPS. |
| `smoke` | Verify frontend/API source SHAs, data version, calculations, routing, public exclusions and optional public URL. |
| `backup` / `restore` | Host-side binary-safe logical dumps / restore to an isolated test target or explicitly named demo target. |
| `demo-start` / `demo-stop` | Routine start/health check or stop project tunnel/cluster containers, preserving data. No backup scheduler required. |
| `evidence` | Optional helper for collecting safe demonstration results. A manual evidence checklist is sufficient. |
| `cluster-rebuild` (optional) | Require verified fresh backup and explicit `--confirm-cluster stellar-atlas-demo`; delete/recreate only that cluster; regenerate secrets/roles and restore. |
| `teardown` (optional) | Stop public access; back up; remove only named project infrastructure. Keep host backups/state unless separately requested. |

Each action supports `--json` and `--help`; operations emit start/end/result and bounded diagnostic hints, excluding secrets. Make actions resumable/idempotent where defined. Implement helpers before their first call; commands in this plan describe the final executable interface, not pre-existing scripts.

## 2. Canonical data, persistence, and API contracts

### 2.1 Identity, units, and coordinates

- Gaia IDs stay decimal **strings** everywhere: CSV reader, API, TypeScript, URLs, database text columns and JSON. Never pass them through JavaScript Number.
- Special object ID `sun`, position `(0,0,0)`. It does not add a catalog record or affect catalog counts. Sun fields without meaning at the origin are null.
- Source positions: Galactic Cartesian parsecs. Database/API calculations: float64. Renderer: float32 copies.
- `PC_TO_LY=3.261563777`; `C_KM_S=299792.458`; one Julian year is 31,557,600 seconds. Use these constants in shared calculation tests and return `model_version=constant-speed-v1`.
- Parse source `dist_50`, `dist_16`, `dist_84` as kpc and multiply by 1000 for pc. Check `norm(x,y,z)` against `1000*dist_50` with relative tolerance `1e-5`.
- Three.js mapping is `(scene_x,scene_y,scene_z)=(galactic_x,galactic_z,-galactic_y)`. This is a rotation, not an axis reflection. Orient labels/reference plane consistently and test basis vectors.
- Snapshot ID: `gcns-edr3-20261013-20271720`; source checksum is the full 64-character value. Revised transformations append a deterministic transform-version suffix; never overwrite an existing snapshot's bytes.
- Bootstrap aliases: only `Proxima Centauri` → `5853498713190525696` and `Barnard's Star` → `4472832130942575872`, after P03 checks those cross-identifications against SIMBAD and records URLs. If an alias check conflicts, omit the alias and expose the source ID; never relabel coordinates. No bulk SIMBAD scrape or synthetic famous-star rows.

### 2.2 Catalog database

Create database `stellar_catalog` and schema `catalog`. Schema-owner/migration/import role `catalog_writer`; runtime role `catalog_reader` has CONNECT/USAGE/SELECT only. Revoke public schema CREATE and default public grants. Apply matching default privileges for future tables.

| Table | Required fields and invariants |
|---|---|
| `snapshots` | `id text PK`, raw checksum, transform version, schema version, epoch, source URL, provenance JSONB, total rows, in-scope rows, created_at timestamptz, `status` in staging/ready/failed. Ready snapshots immutable. |
| `stars` | `(snapshot_id,source_id) PK`, ordinal integer unique within snapshot, float8 x/y/z/distance_pc/distance_ly, nullable G/BP/RP/color_index, distance_p16_pc/p84_pc; finite/positive/order constraints; source ID regex. |
| `aliases` | snapshot/source FK, alias, normalized_alias; uniqueness per normalized alias and source. No arbitrary user-written aliases. |
| `map_chunks` | snapshot/chunk PK, count, ordinal/radius bounds, format version, gzip bytea, uncompressed/compressed SHA-256 and sizes. |
| `active_snapshot` | singleton boolean PK constrained true, snapshot FK; only ready snapshot can be activated by importer transaction. |

Indexes: source text prefix index; `(snapshot_id,distance_pc,source_id)`; `(snapshot_id,ordinal)`; lowercase alias prefix index. No geospatial extension is needed. Neighbor queries bound candidates to the chosen snapshot/radius and sort squared float64 separation, stable tie-break by source ID; catalog size is small enough to benchmark this first. If NF05 fails, precompute five neighbors for the default subset during import; retain exact query semantics for other radii. This is the prescribed performance remedy, not an alternative architecture.

No database migrations run automatically inside API startup. A single migration Job runs before application rollout and holds a database advisory lock. All changes are additive/backward-compatible; Alembic downgrade is disabled in automation.

### 2.3 Journey database

Create `stellar_journey`, schema `journey`, migration role `journey_owner`, runtime DML role `journey_app`. Grant no catalog DB access. Store:

`journeys(id uuid PK, idempotency_key uuid UNIQUE NOT NULL, request_hash text NOT NULL, snapshot_id text NOT NULL, origin_id text NOT NULL, destination_id text NOT NULL, origin_position_pc float8[3] NOT NULL, destination_position_pc float8[3] NOT NULL, distance_pc float8, distance_ly float8, speed_fraction_c float8 CHECK 0.001<=value<=0.5, speed_km_s float8, duration_julian_years float8, model_version text, created_at timestamptz, expires_at timestamptz)`.

Frozen positions/results allow old shared summaries to survive catalog changes. No IP, email, cookie identifier, user title, or personal field is stored. Shared UUIDs are public access links, not private authorization credentials.

Retention CronJob runs daily at `0 3 * * *` UTC, marks expiry by timestamp (no write required) and deletes records older than expiry+7 days in batches of 1000. Apply an index on expires_at. GET returns 410 during the 7-day expired grace period, then 404 after purge.

### 2.4 API conventions

Internal service port 8000; public paths are routed through the web gateway:

- `/api/catalog/…` strips `/api/catalog` before reaching Catalog.
- `/api/journey/…` strips `/api/journey` before reaching Journey.
- All feature routes begin `/v1`. Health routes are `/health/live` and `/health/ready`; metrics `/metrics`; OpenAPI `/openapi.json` is local/internal only in demo.
- Success is JSON except binary map chunks. Error shape: `{"error":{"code":"…","message":"…","request_id":"…","details":[]}}`.
- Use 400 malformed query/view state, 404 missing record, 409 incompatible snapshot/idempotency conflict, 410 expired journey, 422 valid JSON with invalid fields, 429 rate limit, 503 unavailable dependency. Do not leak stack traces/DSNs.
- `X-Request-ID` is generated/replaced at the gateway and propagated to internal requests; validate maximum 64 characters. All timestamps UTC RFC3339; browser localizes display.
- Bounds: body 4 KiB, search query 100 characters, result limit 1–100 (search UI 20), speed numeric finite, IDs `sun|[0-9]{1,20}`, snapshot/chunk paths constrained to known DB keys. Reject unknown JSON fields, NaN, Infinity and same endpoints.
- Catalog and Journey expose `/v1/meta` with service name, source SHA, image release ID, schema version, readiness and active snapshot where applicable. No credentials or host paths. Web exposes `/version.json` built with the same source SHA.

Catalog endpoints:

| Route | Input and response |
|---|---|
| `GET /v1/snapshots/active` | Current immutable snapshot ID, epoch, checksum, source/citation/license links, counts, maximum map radius, map format. |
| `GET /v1/snapshots/{snapshot}` | Metadata for a specific retained ready snapshot; shared old views resolve this rather than silently using the new active snapshot. Register the literal active route before this parameter route. |
| `GET /v1/snapshots/{snapshot}/stars` | `q`, `radius_ly`, `limit`, `cursor`; exact ID first, alias prefix next, ID prefix next; order distance then ID; response items and opaque validated cursor. Empty q gives nearest list. |
| `GET /v1/snapshots/{snapshot}/stars/{id}` | Full allowed profile; `sun` special response. Nullable measurements explicit. |
| `GET /v1/snapshots/{snapshot}/ordinals/{ordinal}` | Resolve a renderer ordinal into the same full profile. |
| `GET /v1/snapshots/{snapshot}/stars/{id}/neighbors` | `radius_ly`, `limit=5`, return both `separation_ly` and `distance_from_sun_ly`. |
| `POST /v1/snapshots/{snapshot}/positions` | Internal-only batch of 1–2 IDs; return frozen positions. Gateway must block this route. Journey never reads Catalog's database. |
| `GET /v1/snapshots/{snapshot}/map` | `radius_ly`; exact total count, complete chunk descriptors whose minimum radius intersects request, and snapshot metadata. Counts exclude Sun. |
| `GET /v1/snapshots/{snapshot}/chunks/{chunk}.bin` | Content-Type octet-stream, Content-Encoding gzip, immutable Cache-Control, ETag over bytes. Conditional GET supports 304. |

Journey endpoints:

| Route | Input and response |
|---|---|
| `POST /v1/estimate` | `{snapshot_id,origin_id,destination_id,speed_fraction_c}`; validate, fetch both positions from Catalog, calculate float64 results; no persistence. |
| `POST /v1/journeys` | Same body plus required UUID `Idempotency-Key` header; recalculate server-side; store immutable result; return 201/Location or 200 for matching idempotent retry. Reused key with different payload is 409. |
| `GET /v1/journeys/{uuid}` | Frozen result plus expiry/model assumptions. Browser builds share URL using its current origin. |

Journey-to-Catalog HTTP client: explicit internal base URL, connection timeout 1 s, total request timeout 3 s, one retry only for connection/reset/503 failures, no redirects, no user-supplied URL, propagate request ID. Source snapshot must match the requested immutable ID. Do not silently compute using a new active snapshot.

### 2.5 Binary map format and cache

Sort baseline stars by `(distance_pc,numeric source_id)`, assign ordinal starting at 1. Ordinal 0 is reserved for Sun, which is generated client-side. Chunk at 8192 records, including final short chunk. Each record is 24 little-endian bytes:

`uint32 ordinal; float32 x_pc; float32 y_pc; float32 z_pc; float32 g_mag; float32 bp_minus_rp`.

Only the last two fields may be quiet NaN for unavailable photometry; position fields must be finite. Missing display fields render neutral white and default point size. No numeric Gaia ID is packed into float32 or JavaScript Number. A selected ordinal is resolved through its API endpoint.

Generate gzip deterministically (`mtime=0`), ETags and manifest checksums. Store compressed bytes in PostgreSQL so API replicas need no shared filesystem. Fetch only intersecting chunks with a small concurrency limit and release Three.js buffers on unmount. Start with straightforward bounded storage; add a Worker/LRU cache only if measured memory or responsiveness requires it. A boundary chunk may contain out-of-radius objects; shader/picking filters exclude them. Draw counts and list counts must agree.

### 2.6 Atomic importer algorithm

1. Verify raw and archive checksums, expected header, source/schema/version and declared baseline row count before DB writes.
2. Parse IDs as strings, reject duplicate IDs, nonfinite positions/distances, nonpositive distances, reversed percentiles and norm/unit mismatch. Normalize missing photometry to null.
3. Produce normalized rows, deterministic ordinals/chunks, and report. Check baseline counts against PRD; arbitrary future candidate checks use its separately reviewed manifest, never hardcode every future release to 331,312.
4. Acquire `pg_advisory_lock` for this importer. If same snapshot already ready with matching checksum/transform/chunks, verify and reuse its rows. With `--activate`, atomically move the active pointer to it even if another newer snapshot is currently active; without that flag leave the pointer unchanged. This is required for data rollback, not a duplicate-row import.
5. Insert a staging snapshot and COPY rows in a transaction; build indexes/aliases/chunks; compare all output counts/checksums. No partially staged data is visible via active APIs.
6. Set snapshot ready and, only when `--activate` was supplied, switch singleton active pointer within the same final transaction. Migration/import Jobs in a release use `--activate` for the release's exact declared data version; validation-only operations do not. Commit only after validations. On exception roll back; record a sanitized failure report outside the active snapshot.
7. Never delete prior ready snapshots during activation. Data deletion is an explicit maintenance command which first checks journey retention and backups. This release retains all imported snapshots; no automatic catalog pruning.

## 3. Platform, security, release, and operational contracts

### 3.1 Ports, namespaces, and ownership

| Resource | Namespace / host port | Owner |
|---|---|---|
| kind cluster + default networking | `stellar-atlas-demo`, kube-system; API loopback only | bootstrap scripts + pinned vendor files |
| Application resources | `stellar-atlas` | Argo; local bootstrap overlay only before Argo is enabled |
| PostgreSQL + 10 GiB PVC | `stellar-data`, service 5432, no host port | Terraform |
| Prometheus/Grafana/kube-state-metrics | `stellar-monitoring`, local port forwards 9090/3000 | Terraform |
| Argo CD | `argocd`, local port forward 8081 | vendored namespace-scoped installation + Terraform RoleBindings |
| Public gateway | frontend NodePort 30080 → host `127.0.0.1:8080` | kind mapping + Argo application Service |
| Terraform state/backups/secrets | `.local/terraform`, `.local/backups`, `.local/secrets` | host operations; never Git |

Use one control-plane node with Linux containers and the pinned node image.
Use kind's default CNI; keep the API and mapped gateway on loopback. Check local
port/CIDR conflicts if startup reveals one. Do not add a custom CNI or automatic
multi-range network-selection framework for the baseline course demo.

No ingress controller is needed: the web gateway proxies the APIs. This provides public routing through Kubernetes; a separate Ingress demonstration is outside the default scope unless supplied course material requires it.

### 3.2 Small local Kubernetes configuration

Use one replica each for Web, Catalog and Journey, plus one PostgreSQL instance
with its persistent volume. Keep the planned modest per-container CPU/memory
requests/limits and basic liveness/readiness probes. Temporarily scale an API to
two replicas for the course demonstration, then return to one. No PDB, HA claim,
quota-tuning exercise or custom rollout deadline is required.

Use kind's local-path storage. Pod/container restarts should retain data; cluster
deletion can destroy it. Keep an external host dump before a destructive action.
Routine stop preserves the cluster, volumes and local Terraform state.

### 3.3 Basic security and private services

Use non-root app containers, ordinary Kubernetes security contexts and resource
limits/probes. Add writable temporary paths as needed; do not spend time forcing
every component into a custom hardened image. Keep DB/admin/metrics ClusterIP-only
and out of the public gateway. Block internal positions, docs and mutation/import
routes at the gateway; use same-origin API calls and standard security headers.
Keep a simple request/body limit, with no per-client quota framework.

Reuse P04's role-specific credentials under ignored `.local/secrets`; keep values
out of source, images, Terraform state and reports. Generate/apply them through
the existing helpers. Verify permissions at setup or after an access problem,
not as a repeated elaborate audit on every feature change.

Calico, default-deny ingress/egress, detailed RBAC attack matrices and policy
admission detectors are optional. If selected, prove one allowed/denied example;
otherwise record network-policy enforcement as out of course scope, not passed.

### 3.4 Git, images and simple GitOps delivery

- Preserve protected `main`: PRs, up-to-date branch and both existing required
  `ci / quality` and `ci / security` checks, including admins. Use `codex/` branches.
- Keep the existing CI tests/locks/secret scan. Add only focused frontend smoke
  coverage and ordinary image builds as those features arrive; no CI cluster.
- Build four app images from one clean source revision, scan once, publish those
  images to GHCR and record immutable digests plus source/data versions.
- A trusted successful-main workflow may update application manifests on `deploy`
  using the repository token. Keep read-only defaults, scoped write permissions,
  no fork secrets, one release concurrency group and a simple latest-main check.
- Argo follows `deploy`; no inbound cluster credential or self-hosted runner is
  needed. Verify source/version and a real calculation after sync. An image push
  alone is not a running deployment; an offline host is reported as unavailable.
- Retain the previous deploy commit. Demonstrate rollback with a normal Git revert
  and resync; no automated rollback state machine, fault-toggle workflow or release
  race campaign is required. Never force-push or automatically downgrade schemas.
- Cosign, Sigstore/OIDC, SBOM attestations, custom promotion-policy engines and
  release artifact cleanup workflows are optional. Do not implement them by default.

### 3.5 Minimal DevSecOps checks

Keep the passing Gitleaks/full-history publication checks. Demonstrate one image
scan with the already selected Grype tool before publishing release images.
Review actionable high/critical findings and fix relevant problems; never label
an unrun/failed scan as passed. Do not publish actual secrets or deliberately
unsafe images. Use one clearly fake local fixture to demonstrate a rejected gate.

Basic manifest review checks non-root execution, probes/limits, private DB/admin
surfaces and absence of embedded secrets. Plain commands and a short report are
sufficient. No required coverage percentages, scanner exception-expiry parser,
scanner DB-age framework, duplicate scanner stack or self-test for every tool.
Optional SAST/dependency/IaC scans become required only if supplied course material
asks for them. Existing required GitHub checks are never disabled to simplify work.

### 3.6 Minimal Argo setup

Use one non-HA Argo installation with a local-only UI and an AppProject scoped to
this repository and application namespace. Platform resources remain Terraform's
responsibility. Run migrations/import before runtime rollout; use simple ordered
Jobs or manual bootstrap initially. Add the daily retention CronJob from P07.

Prove one real sync and a Git-driven update/rollback. A custom PostSync smoke
image, exhaustive can-i matrix, retry framework and component-by-component tuning
are not baseline requirements. Use a documented smoke command after deployment.

### 3.7 Basic monitoring, backup and public demo

Use local Prometheus/Grafana with a small dashboard for requests, errors, latency
and pod health. Keep monitoring private. Alert rules, automatic report collection
and extensive capacity/observability frameworks are optional.

Take manual binary-safe `pg_dump -Fc --no-owner --no-acl` backups of both databases
to ignored `.local/backups/`, with a small checksum/data-version note. Do this
before destructive changes and once before assessment. Restore once into an
isolated test database/target and verify row count plus a saved journey. An
automatic 30-minute scheduler, backup rotation engine, fixed RPO/RTO and complete
cluster destruction/reconstruction are optional; do not delete the working demo
merely to satisfy the old plan.

Cloudflare Quick Tunnel forwards HTTPS to the Kubernetes gateway at
`http://127.0.0.1:8080`. Record the actual temporary URL and verify it once from
a phone/external browser. No account, paid service/domain, AWS, Tailscale or Vercel.
Disclose that the host, Docker, cluster, internet and tunnel must stay running.
Check that DB/admin routes are not public; no external availability monitor or
automated multi-outcome verification service is required.

## 4. Implementation phases

Each phase records its actual commands, exit results and source commit in `.local/reports/phases/Pxx.json`. Update `docs/ACCEPTANCE.md` with sanitized links/results. Make one logical commit per completed phase; after remote protections are enabled, deliver changes through PRs. Never commit an invented green status.

### P00 — Resolve prerequisites and freeze the execution environment

**Depends on:** nothing. **Output:** a verified host/account/toolchain inventory.

1. Read this plan, the PRD, existing validation reports/scripts and any applicable AGENTS.md in the working directory/ancestors. Preserve originals and unrelated files.
2. Inspect current Git state and remote before initializing anything. At the planning checkpoint none existed; execution must recheck rather than assume.
3. Inventory CPU, RAM, free disk, OS, WSL2 and Docker settings from the user's normal session. Treat sandbox access denial separately from a host problem. Record the reference hardware/browser for later measurements.
4. Start the existing Docker Desktop in Linux-container mode. If missing, use the official educational/free installer only after host prerequisite authorization. Verify Docker server responds, a pinned Linux hello container runs, named volumes work, and `docker compose version` succeeds. Do not change Windows security settings to bypass an access error.
5. Verify loopback ports 8080, 8081, 9090 and 3000 are free. If occupied by this project, reuse/reconcile its recorded process. If occupied by another application, fail with its exact port and require the operator to free it; do not kill unrelated processes or silently change documented ports.
6. Confirm GitHub authentication using `gh auth status` and `gh api user`. Human completes login/MFA if needed. Use authenticated personal owner `Jyot-Kikani` and existing repository `DevOps_Assignment`; inspect and preserve existing contents/history/remote. Do not create a replacement repository or change visibility automatically. No organization/billing prerequisite.
7. Confirm GitHub Free/public-repository usage, standard hosted runner availability, current GHCR free policy, no purchased runner/marketplace action/paid storage, and zero overage budget where configurable. Capture sanitized evidence. Refuse an account change that requires a paid upgrade.
8. Prepare the pinned portable `cloudflared` Windows executable, verify its publisher's SHA-256 and version, and freeze the corresponding Linux binary metadata. Cloudflare Quick Tunnel requires no account, login/MFA, auth key, DNS configuration or purchased domain. Tailscale installation/sign-in is not a prerequisite.
9. Record the temporary-URL lifetime and absence of an uptime guarantee. P00 checks binary readiness and the accountless routing contract; an actual public URL and external application smoke remain unverified until P16, when the local Kubernetes gateway exists. Do not start a placeholder public site or claim it proves the application deployment.
10. Create the stdlib-only initial `tools/run.py` bootstrap, `.local/tools` and inventory output. Download approved native tool binaries from official releases; verify published checksums and record them. Use portable Node 24.22.0 and `npm.cmd`, avoiding the installed Node 22 and PowerShell npm script execution-policy issues.
11. Resolve the approved tool/library versions and image digests according to section 0.3; create the lock manifest, direct dependency declarations, hashed Python locks, frontend lock and vendored-platform checksum list. For tools without an upstream checksum, verify publisher/release metadata, record the artifact hash and mark its provenance mechanism explicitly.
12. Check Calico 3.33's published Kubernetes support includes 1.35 and verify selected kind node digest exists. Save source URLs and metadata; do not claim integration compatibility until P12 passes.
13. Rehash the saved CSV. If absent, recover the exact archived snapshot from a team copy/data release if available. A new GAVO query is a **new candidate**, because row order/content can change; normalize/validate and deliberately create a new lock manifest rather than pretending it has the old checksum. Do not use the existing `validate_catalog.py` blindly: it downloads and overwrites its output.

**Exit:** normal-session Docker and required tools work; source snapshot is preserved; owner/repo and free tunnel path are known; exact versions/provenance are frozen. Any missing human authentication or machine resource is a named prerequisite blocker, not a deferred architecture choice.

### P01 — Establish repository governance and scaffolding

**Depends on:** P00. **Output:** repository structure, reproducible scripts, contribution rules.

1. Create the layout in section 1 without replacing existing `validation/` or `design/`. Add `.gitignore` before staging: ignore `.local/`, `.env*` except `.env.example`, Terraform state/plan files, node_modules, Python environments, raw CSVs/binaries, local dumps, screenshots/traces and generated coverage files.
2. Add `.dockerignore` for the same sensitive/unrelated paths. Build contexts use explicit COPY allowlists; `.dockerignore` is not the only secret boundary.
3. Create MIT license for original software only, `data/LICENSE-NOTICE.md` for upstream data, security reporting guidance, contribution/PR templates, and ADRs documenting the frozen decisions.
4. Initialize Git with branch main if no repository exists. Use the user's configured Git identity; do not invent an email. Initial commit contains planning/scaffolding, sanitized feasibility reports and mockups, not the raw 50 MB catalog.
5. Implement `ops.ps1` and `tools/run.py` dispatch/help, repository path discovery, subprocess wrappers, JSON reporting, timeout handling and context/path guards. Implement `doctor` and `tools-lock` completely.
6. Configure project-local Python environments for APIs/importer/ops; install only from committed lockfiles. Configure frontend npm scripts `dev`, `build`, `lint`, `typecheck`, `test`, `test:e2e` and root operation aliases.
7. Write README prerequisites and reading order, `.env.example` and public configuration schema. Add `tools/operator.example.json` listing GitHub owner/repo, local tool paths and public URL key; put actual machine values only in ignored `.local/operator.json`.
8. Commit phase output and verify a fresh temporary clone can resolve documented commands and validate locks without reading the original working directory's environments.

**Exit:** no secrets/raw data staged; documented command dispatcher works from a different current directory; lockfiles are reproducible; existing evidence is preserved.

### P02 — Define contracts, common primitives, and executable acceptance skeleton

**Depends on:** P01. **Output:** stable schemas and test fixtures before feature implementation.

1. Create typed API models and OpenAPI definitions for every endpoint in section 2.4. Define examples, validation bounds, errors, request IDs and version metadata. Generate committed OpenAPI JSON from service models; CI later compares regeneration to Git.
2. Generate TypeScript API types from committed OpenAPI using a pinned generator. Keep transport wrappers handwritten and small. Do not duplicate numeric IDs as TypeScript numbers.
3. Implement `stellar_common` ID validation, unit constants, float64 distance/time calculations, error envelopes and redacted structured logs. Put a pyproject.toml in `packages/python/`, and one in each service/job directory. Python source modules are `stellar_catalog`, `stellar_journey`, and `stellar_importer` under their respective src directories. Build/install the common wheel into each image; no runtime cross-directory imports from an unmounted repository.
4. Add independent mathematical test oracles: 3-4-5 position triangle, Sun-to-known-position conversion, identical endpoints, very small distance, 0.001c/0.5c limits, NaN/Infinity rejection, and 1 Julian-year unit conversion. Do not merely assert that two copies of the same formula agree.
5. Define the map-format schema, binary encoder/decoder golden fixture, source-ID-string fixture above 2^53, gzip determinism fixture and renderer coordinate-basis tests.
6. Create a small attributed catalog fixture from existing known rows plus explicitly synthetic edge-case rows labeled as fixtures. Its manifest declares its own count/checksum. Never require every test fixture to contain 331,312 rows.
7. Create `docs/ACCEPTANCE.md` with FR/NF/DV IDs, test/evidence references and initial `not run` status. Add the release JSON schema and phase-report schema.

**Exit:** contracts validate, type generation is repeatable, unit/golden fixtures pass, no endpoint/schema field is left unspecified.

### P03 — Seal the dataset, provenance, and distributable asset

**Depends on:** P02. **Output:** pinned input reproducible outside this laptop.

1. Copy the baseline into ignored `.local/data/raw/` without mutating the existing validation source. Verify full checksum and schema again.
2. Implement `data-seal`: deterministic gzip with timestamp zero, streaming SHA-256, raw/archive byte sizes, fixed schema, source URL, fetched/validated dates, GCNS paper and Gaia EDR3 epoch, count report and transformation version in `data/snapshot.lock.json`.
3. Implement the baseline validator specified in section 2.6. Keep a human-readable report of optional photometry coverage. Treat missing optional photometry as null, not row rejection or zero magnitude.
4. Verify the two initial aliases against recorded SIMBAD identifiers/cross-identifications. Store URLs and checked mapping in aliases.sources.json. If a mapping cannot be verified, omit that display alias and retain ID search; record the reason. This does not block the core catalog.
5. Preserve the provider's Gaia/GCNS credit and data-license notice with citations and an explicit transformed-data notice. ESA's official `https://www.cosmos.esa.int/web/gaia-users/license` was successfully fetched during planning and states CC BY-NC 3.0 IGO; retain that license/link, ESA/Gaia/DPAC attribution, the EDR3 credit instructions and GCNS paper citation. This release is educational/noncommercial; software MIT licensing does not relicense the catalog. Archive the notice and retrieval date with the data asset. If a provider page is temporarily blocked, use the retained official notice and its archive credit page; do not substitute an unrelated license or introduce commercial reuse.
6. Implement `data-publish` to create an immutable public GitHub data release `data-gcns-edr3-20261013`, upload `gcns-required-fields.csv.gz`, `snapshot.lock.json`, the validation report and data notices. If an exact release/asset exists, compare hashes and reuse; never overwrite changed bytes under the same data version.
7. Publication occurs in P15 after public access for the existing repository is explicitly established. Until then test publication with a local staging directory. The eventual URL is `https://github.com/<owner>/DevOps_Assignment/releases/download/data-gcns-edr3-20261013/gcns-required-fields.csv.gz`. The P03 sealed lock retains its historical `stellar-atlas` URL template to preserve immutable bytes; ADR 0004 supersedes that planned destination. Resolve the actual new URL into a separate resolved lock after publication; never rewrite the sealed archive/notices merely to rename a repository.
8. Keep large data out of Git/LFS/Actions artifact storage. Test download-to-temp, checksum verification and extraction using a fresh local cache; after P15 repeat against the actual release URL.

**Exit:** deterministic, validated local archive and complete provenance exist; publication contract is implemented. Network/rights failure has an explicit safe outcome, never fabricated success.

### Early CI checkpoint — after P03, before P04

Authorized on 20 October 2026. This brings source integration forward; it does not complete P10/P15 or authorize P04–P07 in the CI setup chat.

1. Inspect the existing `Jyot-Kikani/DevOps_Assignment` repository, authentication, remote history and permissions. The user changed it from private to public on 20 October; preserve that verified public state, contents and origin. No new repository.
2. Scan complete Git history and tracked/staged files for secrets, raw catalogs and private local evidence before the first push. Keep reviewed account-level zero-paid-usage budgets. Use free standard hosted runners for the public repository, bounded storage and no paid runners, budget increases or purchased credits.
3. Add basic `ci.yml` with `quality` and `security` jobs on main pushes and PRs to main. Use pinned actions, standard Ubuntu runner, frozen dependencies, read-only contents permissions and bounded timeouts/concurrency. Run existing unit/contract/frontend/type/lint/build checks and full-history secret/exclusion checks. Do not claim unimplemented database/E2E/security gates.
4. Verify an actual GitHub run and record its URL and exact check names. Continue subsequent feature changes through branches/PRs and extend CI with real integration tests. Following the user's public-visibility change, main protection is active: require both observed GitHub Actions checks and an up-to-date PR; include admins; disable force pushes/deletion; resolve conversations; require zero human approvals. Preserve these rules and verify pending-check blocking and successful merge without bypass. The initial private Free limitation is historical, not the current state.
5. P10/P15 extend the existing checks only as required by the revised course scope below. Deployment, data-release publication, GitOps and public application access remain later phases; signing is optional under ADR 0005.

### P04 — Implement databases, credentials, and migrations

**Depends on:** P02. **Output:** isolated schemas with least-privilege grants.

1. Create catalog/journey SQLAlchemy models, SQL/Alembic migrations and the exact indexes/constraints in sections 2.2–2.3. All datetimes timezone-aware UTC.
2. Implement a database bootstrap command, using admin credentials only to create both databases and four application roles. Role passwords arrive through protected stdin/files, never logs/CLI arguments. Runtime APIs never receive the admin password.
3. Implement `secrets-init` with secure random passwords and a generated local secret file. On Windows restrict its directory to the current user and verify the result; do not print passwords in error reports. Store no secret in Terraform state.
4. Configure PostgreSQL 17 named volume in a database-only Compose profile for development. Kubernetes will use its own PVC later. Disable public database listeners on host; maintenance uses docker/kubectl exec.
5. Implement explicit migration commands with database advisory locks. Make repeated migration invocation a no-op when already at head. Set connection pool size 5/max overflow 2 per API container and database max_connections 60.
6. Test reader SELECT success, reader INSERT/DDL denial, Journey access to Catalog denial, and Catalog access to Journey denial. Test constraints with actual PostgreSQL, not SQLite substitutes.
7. Test a fresh schema, an upgrade from the previous fixture migration, repeat migration, and invalid migration failure without damaging existing rows. Keep only additive migration operations in this release.

**Exit:** both databases migrate cleanly; privilege-denial tests pass; existing data is preserved on restart.

### P05 — Implement atomic catalog import and map preprocessing

**Depends on:** P03, P04. **Output:** fully loaded, independently verifiable catalog.

1. Implement streaming parse/normalize, invalid-data reports, COPY loading, ordinals, aliases and chunk generation exactly as section 2.6 defines.
2. Generate chunk/manifest records, compression and checksums without loading enormous Python object graphs unnecessarily. It is acceptable to sort 331,312 compact records in memory within the import Job's measured limit; fail on OOM rather than dropping records.
3. Load fixture, query it independently, check exact row/chunk counts, float64/float32 tolerances and ordinal lookup. Then import the sealed full baseline and compare the PRD counts.
4. Make importer concurrency safe using advisory locking. Run two fixture import attempts concurrently; exactly one activation occurs and the other verifies/reuses the result.
5. Re-import the same snapshot and assert identical hashes/no duplicate rows. Attempt bad checksum, missing column, duplicate ID, NaN coordinate, wrong kpc conversion and reversed percentile fixtures; active snapshot remains unchanged.
6. Simulate process termination after staging writes but before activation; restart and verify no partial ready snapshot is served. Record SQL queries proving active-pointer integrity.
7. Package importer CLI actions `validate`, `import`, `report`, `smoke`, and `retention` with explicit exit codes; no public HTTP import endpoint.

**Exit:** real full dataset loaded; exact baseline checks and negative atomicity tests pass; browser payload sizes are recorded.

### P06 — Implement Catalog service

**Depends on:** P05. **Output:** all catalog endpoints and profiles.

1. Implement lifespan DB connection handling, health/meta routes, read-only queries and the common error/log/request-ID behavior.
2. Implement active snapshot, search/pagination, profile, ordinal lookup, neighbors, internal position batch, map manifest and chunk endpoints. Enforce allowed snapshot/ID/radius ranges and bounded results before querying.
3. Implement immutable chunk caching/ETags/304/gzip correctly. Return stored compressed bytes without double compression. Confirm browser fetch decodes Content-Encoding into the expected uncompressed array length.
4. Keep map count query exact, cap main map at 100 pc, exclude Sun from catalog totals, and return the synthetic Sun only for explicit detail/position requests.
5. Add Prometheus metrics using normalized route labels, source/dataset version info, latency, query failures and pool utilization. Remove credentials from exceptions/logs.
6. Test all endpoints, unknown/invalid values, null photometry, exact long-ID round-trip, stale snapshot IDs, pagination stability, map/selection agreement and neighbor separation versus Sun distance.
7. Verify a snapshot switch does not invalidate an already returned immutable chunk URL/profile. Snapshot metadata must identify the actual queried version.

**Exit:** OpenAPI matches contract; independent SQL/API comparisons pass; full-data local read timings are recorded, even if optimization is still needed in P22.

### P07 — Implement Journey service and immutable sharing

**Depends on:** P06. **Output:** real service communication and persistent anonymous journeys.

1. Implement lifecycle-managed HTTPX client with section 2.4 timeouts/retry/no-redirect policy, and a separate Journey DB connection pool.
2. Implement estimate using Catalog's positions endpoint. Never accept client-supplied coordinates, distance, duration or remote URL as authoritative.
3. Implement create with required UUID idempotency key, normalized request hash, server-side recalculation and frozen positions/results. Use a DB transaction to handle simultaneous identical keys safely.
4. Implement get/expiry/purge contract. Store nothing that identifies the visitor. JSON fields include calculation assumptions and model version.
5. Add health/meta/metrics and log the propagated request ID across the Catalog call. Do not restart a healthy Journey process because Catalog temporarily fails.
6. Test mathematical oracles, body bounds, identical endpoints, unknown object, mismatched snapshot, Catalog timeout/503, own-DB failure, two-service request ID propagation, idempotency races, 409 reuse conflict, 410 expiry and 404 purge.
7. Verify the two real nearest catalog records yield approximately 6.5867612724 ly separation and 65.867612724 years at 0.1c for this frozen snapshot. Use a tolerance, not rounded mockup values.

**Exit:** estimates and shared records work through HTTP service boundaries; failure behavior and database isolation tests pass.

### P08 — Build the web experience

**Depends on:** P06, P07.

Implement the planned Explore/Journeys/Saved/About routes against real APIs.
Use Three.js point clouds, real coordinates, radius counts, profiles/search,
measurement, playback, local saves and share links. Match desktop/mobile references
and retain basic keyboard/reduced-motion/list fallback behavior. Start with simple
picking/loading; add a Worker or elaborate LRU machinery only if the real view
needs it. Keep ordinary input validation and useful loading/error states.

Checks: automate one explore/select/search flow and one journey/share flow. Manually
check mobile layout, saved items and one unavailable/expired state. Reuse backend
tests; no exhaustive browser/URL/storage/context-loss matrix.

**Exit:** the main product journeys work with real APIs and have concise evidence.

### P09 — Finish local Docker Compose

**Depends on:** P08.

Build the four images with pinned dependencies and non-root app users. Complete
the gateway, deep-link routing, private/internal route exclusions, simple limits
and named PostgreSQL volume. Implement straightforward dev-up/dev-down/smoke.
Keep build contexts free of local secrets/raw files except the verified importer asset.

Checks: one fresh startup, one repeat startup, one container/database restart with
a saved journey preserved, and a gateway check that DB/admin/internal routes are
unavailable publicly. Record useful failures; no outage permutation suite.

**Exit:** a documented command starts the usable local app and stop preserves data.

### P10 — Focused tests and basic security checks

**Depends on:** P09.

Reuse all passing P00–P07 checks. Add focused frontend unit tests and the two
browser smoke flows from P08 to ci / quality as practical. Keep fixture-backed real
PostgreSQL/HTTP tests; full sealed-data checks run only after relevant data/binary/
calculation changes or once before final assessment.

Keep Gitleaks and add one Grype image scan command. Review manifests for basic
ports/secrets/non-root/probes/limits. Demonstrate one rejected fake local fixture.
Use plain checked commands and short logs. No coverage quotas, scanner orchestration,
exception expiry system, custom policy engine or multiple redundant negative suites.

**Exit:** existing CI plus focused new checks pass; a simple bad example is rejected.

### P11 — Prepare ordinary release images and metadata

**Depends on:** P10.

Build once from a clean commit; record source SHA, dataset ID/checksum and four
image digests. Smoke the built images and scan them before publication. Simplify
the existing future release schema/tests to these real fields in this phase;
signer/SBOM fields from P02 are no longer mandatory. Do not invent their values.
Keep old contracts until that explicit update; this plan revision changes no code.

Checks: images start, contain required packages/jobs, and identify the actual source.
Keep reports local; no signing/attestation/artifact-retention framework by default.

**Exit:** usable images and a small truthful release record are ready for P15.

### P12 — Create the small local Kubernetes platform

**Depends on:** P11.

Create/reuse only stellar-atlas-demo with pinned kind/node, default networking,
loopback mappings and local-path storage. Keep existing foundation/runtime Terraform
roots for namespaces, PVC, PostgreSQL and basic platform settings; local ignored
state and generated secrets stay outside Git. Do not install Calico for the baseline.

Checks: node/DNS/DB are ready; Terraform validate/apply then a no-change plan; one
harmless label drift and repair as the IaC demonstration. No disposable CI cluster,
policy matrix, quotas/PDB tuning or automated cluster rebuild is required.

**Exit:** the named local cluster/platform works and a repeat plan is clean.

### P13 — Deploy the application locally

**Depends on:** P12.

Deploy one replica of Web/Catalog/Journey, migrations/import Jobs, private DB
Service/PVC and the daily Journey retention CronJob. Use image digests, basic probes
and resource limits. Keep the gateway as the only user-facing route.

Checks: real catalog counts, search, calculation and share round-trip through the
gateway; one workload restart and a representative private-route denial. Reuse
P04–P07 data/expiry proofs rather than rebuilding their entire test matrix here.

**Exit:** the real-data app works through the local Kubernetes gateway.

### P14 — Add basic monitoring and backup/restore

**Depends on:** P13.

Run local Prometheus/Grafana with a small provisioned dashboard. Take a manual
host-side backup of both DBs and restore once to an isolated target. Verify catalog
count and a saved journey, retaining the original working database.

Checks: one request appears in metrics; the restored sample matches. Record commands
and screenshots. No alerting suite, scheduled backup service or RPO/RTO gate.

**Exit:** metrics and a real non-destructive backup/restore demonstration work.

### P15 — Complete course-sized GitHub CI and publication

**Depends on:** P14.

Use only DevOps_Assignment. Retain the two existing protected-main check names
and policies. Add relevant frontend smoke/image-build checks to the existing jobs;
do not require kind/Calico or a separate environment in CI.

Publish the verified sealed data asset and four scanned images using the existing
free repository/GHCR; verify anonymous access. Keep source/data/digest metadata.
Set up a simple trusted successful-main release workflow and deploy branch. Avoid
new token/account services; signing, SBOMs and automated artifact cleanup are optional.

Checks: one intentionally failing test in an unmerged PR blocks CI, then the fixed
version passes. Reuse the local security rejection from P10; no separate PR for
every detector. Bootstrap publication is not yet a verified deployment.

**Exit:** required CI works and the real data/images are anonymously accessible.

### P16 — Open the temporary public demo

**Depends on:** P15 and healthy local app.

Start the pinned accountless Cloudflare Quick Tunnel to the Kubernetes gateway.
Record the current HTTPS URL and its host/uptime limitations. Stop/start only this
project's tunnel; keep DB, metrics and admin tools private.

Checks: use a phone/external browser for Explore, calculate/share and a private-route
denial. A local curl or assigned hostname alone does not prove external access.

**Exit:** the real Kubernetes app is usable from outside the host over HTTPS.

### P17 — Connect Argo GitOps

**Depends on:** P16.

Install the small non-HA Argo instance with local-only UI and repository/namespace
scope. Track the generated deploy branch; keep Terraform platform ownership separate.
Bootstrap migrations/data before app rollout and preserve the existing database.

Checks: one Synced/Healthy application, correct running source/image/data metadata,
and the public smoke flow. No custom sync-hook or permission-test framework.

**Exit:** GitOps manages the working application and actual running versions match Git.

### P18 — Demonstrate one update and Git rollback

**Depends on:** P17.

Make a small visible change through a protected PR. Let CI build/publish the
images and update deploy; observe Argo reconciliation and verify the running change.
Then revert the deploy change through Git and verify the prior version. Keep schemas
forward-compatible and do not restore the DB as an application rollback.

Checks: retain the PR/run/deploy revision and before/after version screenshot. One
real update and rollback suffice; no fault injection, queued-release races, automatic
rollback controller or multiple offline-release scenarios.

**Exit:** an ordinary update and a Git-based rollback are demonstrated.

### P19 — Summarize basic DevSecOps evidence

**Depends on:** P18.

Show the existing secret gate, one image scan, one safe rejected example, private
DB/admin routing and non-root app settings. Reuse earlier checks and role-denial
results. Review logs/evidence for accidental secrets before submission.

Checks: record actual pass/fail output and fix actionable issues. No new scanner
stack, signing policy, attack matrix or exhaustive hostile-input suite unless the
course explicitly asks for it. Existing working validation remains in place.

**Exit:** the course security demonstrations have clear, limited evidence.

### P20 — Demonstrate basic Kubernetes operations

**Depends on:** P19.

Delete one stateless app pod and observe replacement. Scale one API from one to
two replicas through the deployment config/GitOps and return to one. Show the rollout
and explain the PVC. Reuse the P18 rollback and P05 atomic-import evidence.

Checks: record pod/replica output and observed recovery time. A single-node host
is not HA; there is no required chaos campaign, repeated import interruption or
host-offline/release race demonstration.

**Exit:** pod replacement, scaling, rollout and persistence are understandable and shown.

### P21 — Write the short operating/recovery guide

**Depends on:** P20.

Document clean startup, safe stop, update/rollback, manual backup/restore, tunnel
restart and the common observed problems. Reuse the P14 restore evidence; repeat
only if persistence or schema handling changed. Leave the demo running/stopped as
requested; preserve originals, state, backups and unrelated containers.

Checks: one normal stop/start preserves catalog and journey. Full cluster deletion,
automated reconstruction, destructive teardown and a disaster-recovery engine are
optional and require an explicitly named target plus verified backup if requested.

**Exit:** another student can operate the demo using the guide and existing scripts.

### P22 — Do one final usability and performance review

**Depends on:** P21.

Check the main flows once on desktop and mobile: explore/search/profile, calculate/
share, saved items and a useful error state. Check keyboard access and the list
fallback. Record actual screenshots and the correct 1151/300526 catalog counts.

Record a simple warm page/API timing and whether default-radius movement is smooth.
Fix visible slowness or incorrect behavior; 5-second/30-FPS/500-ms targets are now
advisory, not release-blocking SLOs. No mandatory ten-client 60-second load harness,
full browser/device matrix, repeated fault suite or second machine/clean-cluster
campaign. A clean-clone check is useful once if practical, not an entire new platform.

Checks: focused reruns after fixes and the existing required CI before merge. Reuse
the sealed full-data and browser-byte evidence unless those paths changed.

**Exit:** the app is usable at demonstration scale and actual limits are documented.

### P23 — Package the course submission

**Depends on:** all revised required phases.

Provide a concise architecture diagram, README/runbook, course-topic evidence
table, screenshots, PR/CI/release links, current public URL and a short demonstration
script. Reuse real earlier outputs rather than creating an evidence-collection engine.
Record actual running source/data versions, backup location and host availability.

Checks: review the core FR/NF/DV course criteria and one final public smoke flow.
Report real required gaps honestly. Explicitly optional extensions are out of scope,
not failed gates. No new hardening/measurement infrastructure at submission time.

**Exit:** a clear, working, zero-cost course demo with reproducible core evidence.

## 5. Cross-phase details that must not be improvised

### 5.1 Configuration dictionary

All configuration is parsed/validated at startup. Nonsecret defaults go in `.env.example`/ConfigMaps; secret values come only from the named local/Kubernetes secrets.

| Key | Value/source | Consumers |
|---|---|---|
| `APP_ENV` | `dev`, `ci`, or `demo`; demo cannot use fixture data | All |
| `SOURCE_SHA` | Full checked-out 40-character commit, baked into image | All |
| `RELEASE_ID` | `r<github_run_id>-a<attempt>-<source_sha12>` in release manifests; explicit `local-<sha12>` for local bootstrap | APIs, importer, gateway runtime release config |
| `CATALOG_SNAPSHOT_ID` | Exact locked snapshot/transform version, no implicit latest | Catalog/import/Journey/UI metadata |
| `CATALOG_READER_DSN` | Catalog-reader role secret, own DB only | Catalog |
| `CATALOG_WRITER_DSN` | Catalog schema-owner/import role secret | Catalog migration/import Jobs only |
| `JOURNEY_DSN` | Journey-app role secret | Journey/retention Job |
| `JOURNEY_OWNER_DSN` | Journey migration-role secret | Journey migration Job only |
| `CATALOG_INTERNAL_URL` | `http://catalog.stellar-atlas.svc.cluster.local:8000` in demo; `http://catalog:8000` in Compose | Journey |
| `LOG_LEVEL` | `INFO` demo; no body/header/credential dumps | Python services/jobs |
| `SHARE_RETENTION_DAYS` | 30; expired grace 7 days | Journey/retention |
| `PUBLIC_BASE_URL` | Actual HTTPS tunnel URL in ignored operator config/runbook; GitHub variable only if needed | Public smoke, not baked browser code |
| `GITOPS_ENABLED` | Optional bootstrap flag if the workflow needs it; final demo uses GitOps | Trusted release workflow |
| `PGDATA` | `/var/lib/postgresql/data/pgdata` on Linux PVC | PostgreSQL |
| `EXPECTED_SIGNER` | Optional only if signing is explicitly selected | Optional signing checks |

Web API calls use relative `/api/...` URLs and share links use `window.location.origin`, so a tunnel change does not require rebuilding frontend code. Serve static build `/version.json` with SOURCE_SHA; serve nonsecret `/release.json` from a read-only mounted release ConfigMap containing source SHA, RELEASE_ID, image digests, and dataset ID. Release verification checks both static source identity and this runtime deployment identity.

API metadata includes both `source_sha` and `release_id`. This distinguishes deploying the same images in a retry, controlled fault demonstration, or rollback. No health/readiness metadata is accepted solely from an unauthenticated client request header.

### 5.2 Small release record and rollback

In P11, revise the existing future release contract/tests to require only actual
source/repository/release IDs, timestamp, sealed dataset ID/checksum, four image
digests and compatibility versions. Preserve scientific/API contracts. Signature
identity and SBOM hashes are optional extensions; never fabricate them to satisfy
the P02 draft schema. This documentation change does not modify that schema today.

Keep the previous deploy commit for a normal Git revert and verify the restored
running version. Do not downgrade database schemas or wipe data for app rollback.
Use an ordinary manual smoke check after sync; report an offline host honestly.
Journey's implemented 30-day expiry/7-day grace behavior remains unchanged.

### 5.3 Bootstrap order and command milestones

No command is assumed to exist before its implementation phase. Once created, the canonical checkpoints are:

```powershell
# P00–P03: host/tool/data preparation; no cloud account
python tools/run.py doctor --json
python tools/run.py tools-lock
python tools/run.py secrets-init
python tools/run.py data-seal

# P09–P11: complete local application and checks
.\ops.ps1 dev-up
.\ops.ps1 test
.\ops.ps1 security
.\ops.ps1 images-build
.\ops.ps1 smoke --target local
.\ops.ps1 dev-down

# P12–P14: real local Kubernetes and recovery foundation
.\ops.ps1 cluster-create
.\ops.ps1 platform-plan --root foundation
.\ops.ps1 platform-apply --root foundation
.\ops.ps1 cluster-secrets
.\ops.ps1 platform-plan --root runtime
.\ops.ps1 platform-apply --root runtime
.\ops.ps1 demo-bootstrap
.\ops.ps1 monitoring-up
.\ops.ps1 backup
.\ops.ps1 restore --target restore-check

# P15–P18: public artifacts → local public route → GitOps → verified release
.\ops.ps1 data-publish
.\ops.ps1 public-start
.\ops.ps1 gitops-bootstrap
.\ops.ps1 smoke --target public

# P21: safe restart and reuse the P14 manual restore evidence
.\ops.ps1 demo-stop
.\ops.ps1 demo-start
```

Implement only commands needed for the revised phases, with simple validation and useful `--help`. Optional commands in the original section 1.2 inventory are not a requirement to build extra automation. If PowerShell execution policy blocks a local script, use the equivalent `python tools/run.py ...` action; do not weaken machine-wide policy.

P15's first release may report publication with deployment verification pending. The final demo must show GitOps and a public smoke check; a recorded manual check is sufficient. Do not label an unverified release as deployed. P16 needs a local app, not an already-working Argo instance; P17 needs the already-published deploy ref. This order avoids a circular bootstrap dependency.

### 5.4 CI fixture and production separation

- CI fixtures have their own manifest/count and `fixture=true`. CI Playwright expected counts derive from that manifest; production acceptance uses the exact baseline counts from the PRD.
- The release builder rejects APP_ENV demo + fixture=true. Promotion schema rejects a fixture dataset. The full importer image is built only from the checksum-verified public data-release archive.
- Local CI images use explicit CI/bootstrap tags only inside their documented overlays. The deployed demo uses image digests; signatures are optional.
- CI uses software-rendered Chromium for functional tests; no CI FPS result can be advertised as the reference laptop's hardware result.
- Full real-data validation runs before publication, after relevant data/import/binary/calculation changes and once at final acceptance. Ordinary UI/docs releases reuse the unchanged sealed checksum; PR tests use fixtures and cannot claim new full-data validation.

### 5.5 Failure decisions

| Condition | Required response |
|---|---|
| Docker/WSL query denied only in sandbox | Repeat normal-session prerequisite probe; report access boundary; no speculative reinstall. |
| Host has insufficient resources | Use another existing team machine with this exact configuration; otherwise report a concrete prerequisite failure. No paid replacement. |
| Existing exact GitHub repo/cluster contains unrelated work | Preserve it and report the identity collision; never replace silently. |
| Snapshot checksum changes | Treat as a new candidate/version; retain sealed baseline; never edit expected hash merely to pass. |
| Optional alias/photometry absent | Display ID/Not available; preserve correct coordinates and feature behavior. |
| Required coordinates/unit/schema invalid | Reject candidate; keep active snapshot and prior report. |
| Required image scan unavailable | Record the failed scan and retry; never report a pass or substitute an optional scanner framework. |
| GHCR package private | Make the four intended public packages public after inspecting their contents; reverify anonymously; no cluster PAT workaround. |
| No public tunnel route | Verify pinned cloudflared, local gateway health, owned process/logs, outbound connectivity and the current Quick Tunnel URL. Record any external-service blocker; no cloud purchase or silent hosting change. |
| Public app unreachable during release | Report pending/failed verification and host-start instructions; do not claim deployed or blindly overwrite deploy history. |
| Candidate unhealthy | Use the recorded previous deploy commit for a deliberate Git rollback and verify the previous version. No automatic recovery controller required. |
| Newer deploy commit exists during rollback | Abort stale rollback; do not force push or revert someone else's newer release. |
| PVC/node lost | Verify external host dumps, rebuild exact project cluster and restore; never claim local PVC alone is a backup. |
| Optional network-policy demo selected but denial fails | Report that optional demonstration as failed; do not claim enforcement. It is not required for the default course scope. |
| Public bandwidth slow | Optimize verified chunks/cache/loading; report tunnel timing separately. |
| Free-provider terms change | Recheck whether the already-approved free option remains usable; use local equivalents/declared tunnel contingency, report any unmet public-delivery requirement, never authorize spending. |

## 6. Requirements-to-phase and evidence traceability

| Requirement | Implement | Final verify/evidence |
|---|---|---|
| FR01–FR04 atlas/layers/selection | P05, P06, P08 | P13 real-data UI, P22 rendering/counts/screenshots |
| FR05–FR07 search/profiles/neighbors | P03, P06, P08 | P10 contracts/browser, P22 null/alias/neighbor checks |
| FR08 distance | P02, P07, P08 | Independent triangle and real-object calculation tests |
| FR09–FR11 journeys/playback/sharing | P07, P08 | P10 browser/API, P18 public shared round-trip |
| FR12 share views | P08 | One URL round-trip and representative invalid-state check in P22 |
| FR13 saved items | P08 | Manual saved-item flow and one storage-unavailable check in P22 |
| FR14 observer | P08 | Coordinate-basis test and actual viewpoint demonstration P22 |
| FR15–FR17 resilience/release/accessibility | P08, P09 | P18 release metadata, P22 representative error/mobile/keyboard/reduced-motion checks |
| NF01 zero cost | P00, P15, P16 | P19/P23 dated cost/configuration audit |
| NF02 reproducibility | P01, P09, P12 | Repeat documented startup; one clean-clone check if practical |
| NF03–NF06 performance/transfer | P05, P06, P08 | P22 simple usability/timings; old strict SLOs advisory; retain byte/count correctness |
| NF07 security | P04, P09, P10, P12 | P19 basic gates/ports/grants/runtime evidence |
| NF08 recovery | P12, P17, P18 | P20 pod/rollback timing |
| NF09 atomic data | P05 | Reuse completed P05 failure/activation evidence unless importer changes |
| NF10 persistence | P04, P12, P14 | P14 isolated restore with saved journey; P21 safe restart |
| NF11 expiry | P07, P13 | Reuse completed P07 controlled-clock/retention tests unless behavior changes |
| NF12 availability | P16 | P20 offline/resume; About/runbook/public schedule |
| DV01 microservices | P04, P06, P07, P13 | Service HTTP trace, separate images/deployments and privilege isolation |
| DV02 Docker | P09, P11 | Fresh Compose, non-root app images and recorded digests |
| DV03 IaC | P12 | Apply, no-change replan and one label-drift repair |
| DV04 Kubernetes | P12, P13 | P20 probes/pod replacement/scaling/rollout; policy enforcement optional |
| DV05 CI/CD | P15, P17, P18 | PR gates → built image digests → deploy commit → Argo → public smoke |
| DV06 DevSecOps | P10, P11, P19 | One safe rejected example, image scan and basic runtime/private-route settings |
| DV07 local deployment | P12, P14, P16, P21 | Start/stop, monitoring, resource budget, backup/restore |
| DV08 public URL | P16 | External client reaches actual Kubernetes app over HTTPS |

## 7. Source references and planning checks

Primary documentation consulted on 18 October 2026:

- [GCNS schema and access](https://dc.g-vo.org/gcns/q/cone/info), [GCNS research paper](https://arxiv.org/abs/2012.02061), [INAF catalog project](https://gucds.inaf.it/projects/gcns/).
- [Gaia data license](https://www.cosmos.esa.int/web/gaia-users/license), [EDR3 credits/citations](https://gea.esac.esa.int/archive/documentation/GEDR3/Miscellaneous/sec_credit_and_citation_instructions/). Official license HTML was reachable through a direct request even when the search/browser fetcher returned an access error.
- [kind 0.33.0 release and node digests](https://github.com/kubernetes-sigs/kind/releases/tag/v0.33.0), [kind configuration](https://kind.sigs.k8s.io/docs/user/configuration/).
- [Calico on kind](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind), [Calico Kubernetes support](https://docs.tigera.io/calico/latest/getting-started/kubernetes/requirements).
- [Terraform Kubernetes provider](https://registry.terraform.io/providers/hashicorp/kubernetes/latest/docs/guides/getting-started.html), [Terraform 1.16.6](https://github.com/hashicorp/terraform/releases/tag/v1.16.6).
- [Argo installation/namespace privileges/CRDs](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/), [auto-sync and rollback semantics](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/), [Argo 3.5.5](https://github.com/argoproj/argo-cd/releases/tag/v3.5.5).
- [GitHub Actions free-use rules](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [GHCR billing](https://docs.github.com/en/billing/concepts/product-billing/github-packages), [public image access](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), [release-asset limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases).
- [GitHub token workflow recursion](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [free public-repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
- [Sigstore CI signing and exact identity verification](https://docs.sigstore.dev/quickstart/quickstart-ci/), [Cosign verification](https://docs.sigstore.dev/cosign/verifying/verify/).
- [Cloudflare Quick Tunnel accountless setup and limits](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/), [cloudflared official releases](https://github.com/cloudflare/cloudflared/releases). The original Tailscale-first selection was superseded by the user's decision in ADR 0001.
- [Docker educational license](https://docs.docker.com/subscription-billing/desktop-license/), [Three.js Points](https://threejs.org/docs/pages/Points.html).

Registry metadata queried for pinned application packages: npm official package endpoints for React/Vite/Three/Vitest/Playwright and PyPI for FastAPI/SQLAlchemy/Alembic/psycopg. Runtime compatibility, successful installs, scanner findings and performance are explicitly implementation-phase checks, not findings from writing the plan.

### Original planning-document completion check (historical)

- PRD defines 17 functional, 12 nonfunctional and 8 DevOps acceptance requirements.
- Revised phases P00–P23 cover prerequisites through handoff. P00–P07 evidence is historical; future exit criteria follow ADR 0005.
- External/machine inputs have acquisition rules; no paid fallback is permitted.
- Data source, schemas, units, binary format, APIs, runtime topology, ownership, workflow privileges, bootstrap ordering, rollback, backup and acceptance evidence are specified.
- No application code, installation, cloud resource, Git repository publication or deployment has been executed by this document-writing task.

