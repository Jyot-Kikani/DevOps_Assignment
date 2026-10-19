# Stellar Atlas — Detailed Implementation and Delivery Plan

Version: 1.1 | Frozen design date: 18 October 2026 | Public-access revision: 19 October 2026 | Companion: [PRD.md](PRD.md)

The user selected Cloudflare Quick Tunnel as the primary public-access method on 19 October 2026. [ADR 0001](adr/0001-public-access-quick-tunnel.md) supersedes the original Tailscale-first choice. Other architectural decisions and phase boundaries remain in force.

## 0. Execution rules, scope, and evidence boundary

This is an end-to-end implementation specification, not an instruction to invent a second architecture. Implement phases P00–P23 in order. Complete each phase's exit checks before its dependants. Every product requirement has an implementation phase and final evidence check below.

The plan covers account/bootstrap setup, data, contracts, services, UI, containers, local infrastructure, security, CI/CD, public access, monitoring, recovery, performance, assessment, and handoff. Nothing in scope is assigned to an unspecified later roadmap.

Some values necessarily come from execution: authenticated GitHub owner, available host resources, generated passwords, resolved image digests, and assigned tunnel hostname. The acquisition rule for each is fixed here. They are inputs/results, not open architecture decisions. Do not invent account identities or successful measurements. If a prerequisite is unavailable, record that precise blocker and complete independent work; do not buy a replacement service or silently weaken a security gate.

Writing this plan does not initialize Git, install software, create accounts, publish repositories, or deploy anything. A later implementing agent executes it only when asked to implement. Login, MFA, and account ownership remain with the human. Routine coding and reversible verification do not need new design approval. Destructive operations must target only the explicitly named project resources and follow the backup/path checks below.

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
| Repository | One public GitHub repository named `stellar-atlas`, source branch `main`, deployment branch `deploy`. Reuse an existing exact-name repository only after verifying ownership and preserving its contents. |
| Frontend | React + TypeScript + Vite; direct Three.js renderer managed through React lifecycle; plain CSS; system fonts. No React Three Fiber, state framework, paid UI library, or external font dependency. |
| APIs | Two independently packaged FastAPI services: Catalog and Journey. SQLAlchemy + psycopg, Alembic migrations, HTTPX for the Journey-to-Catalog call. One Uvicorn process per container. |
| Data | Immutable baseline snapshot; normalized PostgreSQL rows and pre-generated gzip binary map chunks. No runtime astronomy API calls. |
| Persistence | One PostgreSQL 17 instance; separate catalog/journey databases and credentials. Catalog API is read-only. No service queries the other database. |
| Saved items | Browser localStorage only. Shared journeys are immutable, anonymous, expiring server records. No accounts. |
| Local development | Docker Compose with frontend gateway, both APIs, PostgreSQL, and one-shot migrations/import. |
| Kubernetes | One-node kind cluster `stellar-atlas-demo`, real Kubernetes, Calico CNI, local-path PVCs. No claim of host-level HA. |
| Public routing | Web container is also the reverse proxy. NodePort 30080 maps to host `127.0.0.1:8080`. No additional ingress controller or cloud load balancer. |
| IaC ownership | kind config/bootstrap owns cluster/CNI; Terraform owns namespaces, platform RBAC, policies, quotas, PVCs, PostgreSQL and monitoring; platform bootstrap owns vendored Argo installation; Argo owns application resources only. |
| Application delivery | GitHub Actions builds/scans/signs images, writes approved digest manifests to `deploy`; local Argo CD pulls that branch. No long-lived self-hosted GitHub runner or inbound cluster credentials. |
| Security tools | Gitleaks for secrets; Bandit for Python SAST; npm audit + pip-audit for dependencies; Grype for image vulnerabilities; Syft for SBOMs; Checkov for IaC; Cosign for keyless release-image signatures. |
| Monitoring | Plain manifests for Prometheus, Grafana, and kube-state-metrics; no Helm/operator dependency. Metrics are local-only. Structured application logs go to stdout. |
| Public tunnel | Accountless Cloudflare Quick Tunnel to the local Kubernetes gateway. No purchased domain. Record the actual temporary URL after each start; no stable-hostname promise. |
| Rollback | Restore previous application manifests through a new commit on `deploy`. Never rely on `kubectl rollout undo` while Argo self-heal is enabled. |
| Database changes | Expand-only/backward-compatible within this release. No automatic schema downgrades or destructive migrations. |

### 0.3 Tool and version policy

These releases were queried from their official release/package metadata during planning; their existence was checked, not their joint runtime compatibility. P00 freezes downloaded checksums and P12 validates the complete combination.

| Tool/library | Baseline |
|---|---|
| Node | 24.22.0 LTS, portable project-local installation; existing Node 22 is not the canonical toolchain |
| Python | 3.13 runtime line; host orchestration supports existing 3.13.5 |
| kind | 0.33.0 |
| Kubernetes/kubectl | 1.35.8 |
| kind node | `kindest/node:v1.35.8@sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0` |
| Calico | 3.33.0, manifest installation, VXLAN |
| Terraform | 1.16.6; Kubernetes provider compatibility band `~> 3.2` |
| Argo CD | 3.5.5, namespace-scoped non-HA installation plus separately installed CRDs |
| React / React DOM | 19.3.1, matching versions |
| Vite / Vitest / Three.js | 8.3.4 / 5.0.5 / 0.186.1 |
| Playwright | 1.64.1, matching bundled Chromium |
| FastAPI / SQLAlchemy / Alembic / psycopg | 0.146.0 / 2.1.5 / 1.20.0 / 3.3.6 |
| PostgreSQL | Official 17 Bookworm image, exact digest frozen before the first build |
| Prometheus / Grafana / kube-state-metrics | 3.15.0 / 13.2.4 / 2.20.0 |
| Cosign / Gitleaks / Grype / Checkov | 3.1.3 / 8.30.1 / 0.120.1 / 3.3.29 |
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

No virtualenvs, raw catalogs, generated binary chunks, database files, Terraform state, credentials, screenshots of private account information, or browser traces enter Git. Small attributed test fixtures and sanitized evidence summaries do.

### 1.2 Host command API

Implement `ops.ps1` as a strict dispatcher to `python tools/run.py <action>` using argument arrays, explicit paths, checked exit codes, and bounded timeouts. `tools/run.py` imports the stdlib-only `stellar_ops` package from its own tools directory. Never use string-built shell commands or `Invoke-Expression`. Resolve repository root from the script path, not the current terminal directory. Reject unexpected Kubernetes contexts before writes. All destructive filesystem targets must resolve underneath `.local/` and pass an explicit path-containment check.

| Action | Required effect |
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
| `cluster-create` | Create exact kind cluster and install verified Calico; wait for network and node readiness. |
| `platform-plan` / `platform-apply` | Terraform initialize/validate/plan/apply using ignored local state and the explicit project context. |
| `cluster-secrets` | Apply generated credentials outside Terraform/Argo ownership, redacting input/output. |
| `demo-bootstrap` | Load locally built images and apply local overlay; migrate/import; complete cluster smoke tests. |
| `monitoring-up` | Apply/provision Terraform-owned monitoring and verify scrape targets/dashboards. |
| `gitops-bootstrap` | Install pinned Argo CRDs/namespaced components, restricted RoleBindings, AppProject, Application; enable only when deploy ref is valid. |
| `public-start` / `public-stop` | Enable/disable only this project's tunnel to port 8080; record URL/status and verify HTTPS. |
| `smoke` | Verify frontend/API source SHAs, data version, calculations, routing, public exclusions and optional public URL. |
| `backup` / `restore` | Host-side binary-safe logical dumps / restore to an isolated test target or explicitly named demo target. |
| `demo-start` / `demo-stop` | Idempotent routine start/verification/backup scheduling / stop scheduler+tunnel+project cluster containers, preserving data. |
| `evidence` | Run safe demonstrations in order and build the assessment manifest; destructive/release demonstrations require explicit action flags. |
| `cluster-rebuild` | Require verified fresh backup and explicit `--confirm-cluster stellar-atlas-demo`; delete/recreate only that cluster; regenerate secrets/roles and restore. |
| `teardown` | Stop public access; back up; remove only named project infrastructure. Keep host backups/state unless separately requested. |

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

Generate gzip deterministically (`mtime=0`), ETags and manifest checksums. Store compressed bytes in PostgreSQL so API replicas need no shared filesystem. Fetch intersecting chunks with concurrency 3, cache at most 32 MiB of decoded arrays in memory using LRU, and release Three.js buffers on unmount/eviction. A boundary chunk may contain out-of-radius objects; shader/picking filters exclude them. Draw counts and list counts must agree.

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
| kind cluster + Calico | `stellar-atlas-demo`, kube-system; API loopback only | bootstrap scripts + pinned vendor files |
| Application resources | `stellar-atlas` | Argo; local bootstrap overlay only before Argo is enabled |
| PostgreSQL + 10 GiB PVC | `stellar-data`, service 5432, no host port | Terraform |
| Prometheus/Grafana/kube-state-metrics | `stellar-monitoring`, local port forwards 9090/3000 | Terraform |
| Argo CD | `argocd`, local port forward 8081 | vendored namespace-scoped installation + Terraform RoleBindings |
| Public gateway | frontend NodePort 30080 → host `127.0.0.1:8080` | kind mapping + Argo application Service |
| Terraform state/backups/secrets | `.local/terraform`, `.local/backups`, `.local/secrets` | host operations; never Git |

Use one control-plane node with Linux containers, pinned node image, `disableDefaultCNI: true`, pod CIDR `192.168.0.0/16`, service CIDR `10.96.0.0/12`. Before creation, reject overlap with host/VPN/Docker ranges. If overlap exists, use the first non-overlapping pod CIDR from `[192.168.0.0/16,172.28.0.0/16,10.244.0.0/16]` and service CIDR from `[10.96.0.0/12,172.20.0.0/16,10.200.0.0/16]`, record choices and patch Calico pool consistently. Do not change an existing cluster CIDR in place.

No ingress controller is needed: the web gateway proxies the APIs. This still satisfies public routing through Kubernetes; an Ingress object is not required by the course list.

### 3.2 Kubernetes resource defaults

| Workload | Replicas | CPU request/limit | Memory request/limit |
|---|---:|---|---|
| Web gateway | 1 | 100m / 500m | 64 / 192 MiB |
| Catalog | 2 | 100m / 500m each | 160 / 384 MiB each |
| Journey | 2 | 100m / 500m each | 128 / 256 MiB each |
| PostgreSQL | 1 | 200m / 1000m | 256 / 768 MiB |
| Migration/import/smoke Job | 1 | 100m / 1000m | 128 / 512 MiB |
| Prometheus | 1 | 100m / 500m | 256 / 512 MiB |
| Grafana | 1 | 100m / 300m | 128 / 256 MiB |
| kube-state-metrics | 1 | 50m / 200m | 64 / 128 MiB |

Cap Argo's non-HA components together at 1.5 GiB limits; disable Dex, notifications and ApplicationSet if unused, vendor that explicit patch. Set application quota to requests CPU 2 cores/memory 2 GiB, limits CPU 5 cores/memory 4 GiB, max 25 pods/10 Jobs. Raise only with a measured resource report and recorded manifest change. Include Kubernetes/CNI/Argo overhead in host measurements; these are app budget settings, not a claim that the complete cluster needs only the table total.

Web/Catalog/Journey rollout: `maxUnavailable:0`, `maxSurge:1`, progress deadline 180 s, termination grace 30 s. One-shot Jobs backoffLimit 1, activeDeadlineSeconds 300 (import 600). API liveness checks process only, readiness checks own DB and required ready snapshot. Journey readiness checks own DB; dependency failure is reported as 503 for calculations, not a liveness restart loop. startupProbe allows 120 s, then readiness every 5 s and liveness every 10 s. Use PDB minAvailable 1 for two-replica APIs; it does not protect against host failure.

PostgreSQL PVC uses kind's local-path provisioner on the node's Linux filesystem. Pod replacement and container stop/start preserve it. **Deleting the kind node/cluster can destroy it.** Never claim a PVC is an external backup. Use host-exported logical backups before rebuild. Terraform storage resources have prevent_destroy; regular stop must not run Terraform destroy or delete PVCs.

### 3.3 Runtime security and network policy

Application namespace enforces Pod Security `restricted` at the pinned Kubernetes version. API/web/job pods: non-root fixed UID/GID 10001 (Nginx uses its image's documented non-root UID), readOnlyRootFilesystem, seccomp RuntimeDefault, drop ALL capabilities, allowPrivilegeEscalation false, automountServiceAccountToken false. Provide writable emptyDir only for explicitly required `/tmp`/Nginx cache. Configure PostgreSQL/Grafana volume ownership using their documented UIDs/fsGroup and restricted-compatible settings. CNI is privileged infrastructure in kube-system with a named exception; do not pretend it is an unprivileged app container.

Terraform creates default-deny ingress+egress in application and data namespaces plus these allows:

| From | To | Allowed |
|---|---|---|
| Host/NodePort traffic | Web | TCP 8080 container port only |
| Web | Catalog, Journey | TCP 8000 |
| Journey | Catalog | TCP 8000 |
| Catalog | PostgreSQL | TCP 5432, catalog-reader credentials only |
| Journey | PostgreSQL | TCP 5432, journey-app credentials only |
| Migration/import/retention Jobs | Their required DB/service | Exact port/labels; separate ServiceAccounts and credentials |
| Prometheus | Catalog/Journey | TCP 8000 metrics |
| Smoke Job | Web/Catalog/Journey | Required HTTP ports only |
| App/data pods needing name resolution | kube-system CoreDNS | UDP/TCP 53 |

Runtime services have no general internet egress. Host image pulls are node traffic, not a reason to grant application pods internet access. Import reads its sealed image asset, not the internet. Argo has separate infrastructure egress for Git/DNS/Kubernetes. Monitoring read permissions are scoped to app/data namespaces and required metrics resources.

Prove policy enforcement with an allowed labeled test pod and an unlabelled denied pod using bounded connect timeouts. If denial does not occur, the phase fails even if NetworkPolicy objects exist.

Web gateway: block `/metrics`, health internals except its own `/healthz`, OpenAPI/docs, Catalog positions batch and any admin/import path from public routing. Default-deny unknown `/api/` routes. Serve frontend SPA routes with asset exclusions. Same-origin browser requests; no wildcard CORS. CSP: self-only scripts/styles/connect, inline styles only if required and documented; frame-ancestors none; nosniff; conservative Referrer-Policy. No external analytics. HSTS only on the public HTTPS route via appropriate proxy handling.

Public request limits are deliberately global because tunnel-provided IP headers are not trusted: gateway general API 10 requests/s, burst 20; Journey estimate 120/min; Journey create 30/min, burst 5; max body 4 KiB. Nginx's single replica gives one effective bucket. Return JSON 429 with Retry-After. Do not add extra gateway replicas without moving limits to a shared mechanism.

Secrets are generated locally using a cryptographic RNG, stored under ignored `.local/secrets/` with access restricted to the current Windows account, and applied using stdin to `kubectl`, never command-line password arguments. Separate admin, catalog writer/reader, journey owner/app, and Grafana secrets. Terraform does not manage secret values; Argo does not manage generated Secret objects. Do not store database values in Terraform variables/state, image layers, manifests, GitHub variables, logs, or evidence.

### 3.4 Git and release model

- `main`: source, templates, tests, docs. Protect with PR requirement, required `ci / quality` and `ci / security` checks, no force push/deletion. Do not require another human approval as a technical prerequisite for a solo maintainer; record peer review when a teammate is available. No automatic main bypass.
- `deploy`: generated, deployable snapshot only: `application/`, `release.json`, `previous-release.json`, signature/SBOM pointers. Argo tracks this ref. No PR checks are attached to this branch, so the built-in workflow token can fast-forward it. No force pushes. Only maintainers and trusted release automation should have write access.
- Same-repository `GITHUB_TOKEN` writes `deploy`; no PAT, second repository, private SSH key or GitHub App is needed. A bot push need not trigger another workflow: Argo polls Git independently. Never add the release workflow to the deploy branch or assume a bot push triggers CI.
- `ci.yml`: pull_request to main and push main; default read-only permissions; no fork secrets; test source, contracts, data fixtures, security and image build. Use checkout persistence false unless needed for the scoped promotion step.
- `release.yml`: workflow_run of successful `ci` on main, plus manual retry for the same successful main SHA. Check trusted repository, triggering event push, head branch main, conclusion success, and latest-main SHA before checkout. Never execute fork-supplied code in a privileged workflow_run job.
- Release concurrency `stellar-atlas-demo`, cancel-in-progress false; stale queued releases exit without publishing/promoting. Recheck source and deploy head immediately before promotion.
- Build all four images for a release in one trusted job: web, catalog, journey, importer. Use the exact source commit and dataset artifact; tag `sha-<fullsha>`; scan local built images; push those exact images; obtain immutable digests; sign+verify each digest with Cosign; attach SPDX JSON SBOMs. No runtime `latest` tags, no rebuild between scan and push, no unscanned artifact promotion.
- Job permissions: `contents:read` by default; release alone grants `packages:write`, `contents:write`, `id-token:write`. Limit token scope to this repository. OIDC is for Sigstore, not AWS.
- Cosign verification identity is exactly `https://github.com/<owner>/stellar-atlas/.github/workflows/release.yml@refs/heads/main` with issuer `https://token.actions.githubusercontent.com`; confirm the workflow_run signing certificate identity in bootstrap and freeze the actual expected workflow identity rather than broadening to `.*`.
- Render Kustomize templates with all four digests, source SHA, dataset/schema/model versions and unique release ID. Run schema and security validation on the rendered output before committing it to deploy. Copy the previous deploy snapshot into previous-release metadata. Create one fast-forward commit; reject concurrent change rather than force pushing.
- Promotion is not deployment success. Verify the running frontend and both API SHAs plus a real calculation through the public URL. A Job inside the cluster also runs smoke checks after sync.
- If the host is offline, mark release verification pending/failed and preserve diagnostics; Argo may apply it when the host resumes. Do not report successful deployment from a successful registry push.

### 3.5 Security gates

Store exact gate settings in `security/policy.yml`. Fail closed when a required scanner cannot run or its database is too old (Grype DB age maximum 72 h for release). PR checks can use a cached DB at most 7 days old but must disclose age; releases must satisfy the stricter limit.

- Secrets: any real/suspected secret is blocking. Gitleaks scans working tree and Git history, with a narrowly scoped fixture allowlist only for intentionally fake detector-test data outside actual release sources.
- SAST: Bandit high-confidence medium/high findings block; all others get a recorded disposition.
- Dependency audit: high/critical direct or transitive dependency findings block unless a specific unexpired reviewed exception exists.
- Images: critical vulnerabilities always block; high vulnerabilities with a published fix block. High without fix must be listed in the report and covered by a narrowly justified exception before promotion. Do not hide them using an ignore-unfixed blanket.
- IaC: Checkov high/critical-equivalent or project-defined mandatory failures block: root/privileged app pods, missing limits/probes, public DB/admin, wildcard app RBAC, mutable app tags, embedded secrets, and unrestricted runtime egress. Add custom checks for pinned digests/signature evidence.
- `security/exceptions.yml` starts empty. An entry must identify finding/tool/resource, rationale, mitigation, maintainer, and expiry at most 14 days. Infrastructure privilege exceptions for Calico and scoped controllers are explicit path/resource exceptions, not global scanner exclusions.
- Actions pinned to full commit SHA; tools verified by upstream checksums. Produce a source/dependency/image SBOM and an evidence report. Never pipe a moving network install script into a shell.
- Scanner self-tests deliberately expect rejection of fake secrets/insecure config; a rejected fixture must not itself make the normal repository scan fail. Never introduce actual credentials or push a vulnerable release to prove a gate.

### 3.6 Argo application ordering

Terraform-created databases, PVCs, policies and generated Secrets must exist before enabling the application. Argo AppProject allows only the public repository and namespace `stellar-atlas`; clusterResourceWhitelist is empty. Bind its application-controller to an explicit Role for application Deployments, ReplicaSets, Pods/logs, Services, ConfigMaps, Jobs, CronJobs, PDBs and Events in that namespace. No Secret, Namespace, PV, ClusterRole or database ownership.

Install Argo CRDs separately and use its `namespace-install.yaml`; grant only the documented same-cluster application RoleBinding. Verify permissions using `kubectl auth can-i --as=system:serviceaccount:argocd:argocd-application-controller ...`. Keep Argo's UI ClusterIP and local port-forward only. Disable anonymous access and replace its bootstrap admin password locally.

Sync waves: catalog/journey migration Jobs -30; importer Job -20; runtime ConfigMaps/Services -10; Deployments 0; retention CronJob 10; PostSync smoke hook after healthy workloads. Ordinary migration/import Jobs have release-specific names, no ttlSecondsAfterFinished (avoids Argo repeatedly recreating a TTL-deleted Job), and are idempotent. Retire old Job resources via Argo pruning after successful new sync.

App auto-sync: prune true, selfHeal true, allowEmpty false, PruneLast true, retry 3 with 5/10/20 s backoff; poll interval 30 s with small jitter. No automatic namespace creation. PostSync smoke uses importer image's `stellar_smoke` module, no service-account token, exact dependency labels, and hook-delete-policy BeforeHookCreation/HookSucceeded. Retain a failed hook for inspection until the next attempt.

### 3.7 Monitoring, backups, and availability

Prometheus scrapes annotated app pods through Kubernetes pod discovery, not a load-balanced Service that hides replica-specific metrics. Scope discovery RBAC to the app namespace. Metrics use route templates and service labels, never star IDs/UUIDs/request IDs as Prometheus labels. Expose request count/error/latency histograms, calculation failures, active catalog row count/version info, import success/duration, and database pool utilization.

Dashboard panels: request throughput, p95 latency, 5xx ratio, ready replicas, restarts, CPU/memory, active dataset count, import status, journey creates/expiry, and release SHA information. Prometheus retention 24 h and maximum 512 MiB data; Grafana provisioned dashboards committed as JSON. No cloud monitoring, Loki, external alerts, or email requirement. Local warning rules: target absent 2 min, 5xx ratio >5% for 2 min with a minimum 20 requests, and ready replicas below desired for 2 min.

Host backups: binary-safe `pg_dump -Fc --no-owner --no-acl` for each database, plus dataset/transform/release metadata and checksum manifest. Implement using Python subprocess byte streams to files; never PowerShell text redirection for binary dumps. Publish a backup directory only after both dumps and manifest checks pass. Back up on demo-start, every 30 min while the demo is running, and before import/migration/rebuild. Keep the latest 7 complete backups; do not remove the last known good backup.

Backups are stored outside the kind node in `.local/backups/`, restricted to the current user. Git ignores them. A second copy on an existing team device/USB is recommended for physical host loss but is not assumed in the local-cluster recovery claim. RPO target while the host backup scheduler is running: 30 min; RTO target for local-cluster rebuild: 30 min with warmed images. Record actual restore time.

Restore first into an isolated `stellar-restore-check` namespace/database instance. Verify dumps, apply fresh roles/passwords, create databases, restore with no owners/ACLs, reapply grants, validate row/chunk hashes and a journey sample, and only then permit replacement of demo data. No migration downgrade, no wholesale Docker cleanup, no deleting unrelated kind clusters or volumes.

Cloudflare Quick Tunnel terminates public HTTPS and forwards only to `http://127.0.0.1:8080`. Run the pinned local `cloudflared` executable without an account, auth key, named tunnel, or purchased domain. Record its actual assigned `*.trycloudflare.com` URL; the hostname changes with each new tunnel process. Visitors need neither an account nor a client. Do not enable public access to administrative ports. Quick Tunnels are intended for testing/demos, have no uptime guarantee, allow up to 200 in-flight requests and do not support SSE; this application does not require SSE. Always report local and public timings separately. The host must be awake, connected, and running the cluster/tunnel. Update all published links and PUBLIC_BASE_URL after each URL change.

## 4. Implementation phases

Each phase records its actual commands, exit results and source commit in `.local/reports/phases/Pxx.json`. Update `docs/ACCEPTANCE.md` with sanitized links/results. Make one logical commit per completed phase; after remote protections are enabled, deliver changes through PRs. Never commit an invented green status.

### P00 — Resolve prerequisites and freeze the execution environment

**Depends on:** nothing. **Output:** a verified host/account/toolchain inventory.

1. Read this plan, the PRD, existing validation reports/scripts and any applicable AGENTS.md in the working directory/ancestors. Preserve originals and unrelated files.
2. Inspect current Git state and remote before initializing anything. At the planning checkpoint none existed; execution must recheck rather than assume.
3. Inventory CPU, RAM, free disk, OS, WSL2 and Docker settings from the user's normal session. Treat sandbox access denial separately from a host problem. Record the reference hardware/browser for later measurements.
4. Start the existing Docker Desktop in Linux-container mode. If missing, use the official educational/free installer only after host prerequisite authorization. Verify Docker server responds, a pinned Linux hello container runs, named volumes work, and `docker compose version` succeeds. Do not change Windows security settings to bypass an access error.
5. Verify loopback ports 8080, 8081, 9090 and 3000 are free. If occupied by this project, reuse/reconcile its recorded process. If occupied by another application, fail with its exact port and require the operator to free it; do not kill unrelated processes or silently change documented ports.
6. Confirm GitHub authentication using `gh auth status` and `gh api user`. Human completes login/MFA. Use the authenticated personal owner and repository `stellar-atlas`; no organization/billing prerequisite. If that exact repository already exists, inspect it and stop before destructive replacement.
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
7. Publication occurs in P15 after the public repo exists. Until then test publication with a local staging directory. Record the exact eventual download URL pattern `https://github.com/<owner>/stellar-atlas/releases/download/data-gcns-edr3-20261013/gcns-required-fields.csv.gz` in the resolved lock after publication.
8. Keep large data out of Git/LFS/Actions artifact storage. Test download-to-temp, checksum verification and extraction using a fresh local cache; after P15 repeat against the actual release URL.

**Exit:** deterministic, validated local archive and complete provenance exist; publication contract is implemented. Network/rights failure has an explicit safe outcome, never fabricated success.

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

### P08 — Build the complete web experience

**Depends on:** P06, P07. **Output:** FR01–FR17 implemented against real APIs.

1. Build app shell/routes `/explore`, `/journeys`, `/journeys/:uuid`, `/saved`, `/about`; use a pinned router or native History API wrapper with back/forward tests. Choose native History API + a small React route switch to avoid another framework dependency. Unknown paths show a 404 with return-home link.
2. Implement typed API client, error-state components, abortable requests, debounced search at 250 ms and stale-response cancellation. Never request an astronomy API from the browser.
3. Build one Three.js Points cloud per chunk, shader clipping by Sun radius and appropriate float32 units. Bound device pixel ratio to 1.5, cap visible labels at 20, use real positions and a neutral style for unavailable color/brightness. Dispose WebGL resources on route changes.
4. Implement camera orbit, zoom bounds, orientation indicator, reference plane, distance rings, Sun and selected-point highlights, one-second fly-to and return-home. Reduced-motion mode jumps rather than animates. Disable unrequested automatic orbit.
5. Implement selection with a screen-space spatial grid rebuilt after camera settles (75 ms debounce) and chunk/filter changes. Use a Web Worker to project/cache large point sets; nearest within 10 CSS pixels wins, then nearest depth. Resolve its ordinal through Catalog. Do not create a separate DOM element/mesh per star.
6. Implement radius presets, exact counts, progressive chunk loading with concurrency 3/LRU cache, aborts and progress. Switching filters cannot retain an out-of-radius selectable point unnoticed; selected profile stays open with an explicit outside-current-radius label.
7. Implement profile/search/neighbor panels and null handling, proper distance labels and scientific notices. Alias results must resolve to the same Gaia ID as their plotted point.
8. Implement two-object distance line, Journey selectors/result panel, speed slider+numeric input, 20-second illustrative playback, scrubber and progress years. Inputs/route state remain synchronized and invalid calculations show actionable errors.
9. Add viewpoint movement to a selected star with observer badge and persistent Sun-centered filter explanation. Preserve relative geometry; do not recompute fictitious temperature or claim true apparent sky brightness.
10. Implement local bookmarks/saved journeys with versioned storage key `stellar-atlas.saved.v1`, caps/deduplication, storage-unavailable fallback, item removal and clear confirmation.
11. Implement shared views using URL fragment JSON encoded base64url with schema version and maximum 4 KiB. Validate finite camera/target bounds, known radius/layer values, snapshot/object IDs and observer; ignore unexpected keys. Shared journey URL uses the persisted UUID path.
12. On opening an expired/deleted shared journey, show 410/404 appropriately. Saved local summaries can still display frozen values; do not promise the server record is permanent.
13. Implement responsive layouts, keyboard navigation/focus restoration, sufficient contrast, text legends and a usable list/detail mode without WebGL. Handle lost WebGL context with recovery/list fallback.
14. Add `/about`, release SHA/version banner, dataset/source/citation/license content, scientific assumptions and host-availability statement. Do not copy invented values or geometric placements from generated mockups.
15. Test desktop/mobile user journeys, back/forward, refresh of deep links, share-link round-trip, invalid URL data, reduced motion and no-WebGL fallback.

**Exit:** every FR has working behavior and a browser test/reference; no mocked API remains in the release path.

### P09 — Complete Docker Compose development and operational commands

**Depends on:** P08. **Output:** reproducible local application startup.

1. Complete four Dockerfiles with pinned bases/dependencies, explicit non-root users, read-only-compatible filesystems, health commands and OCI labels. Web uses a Node builder and Nginx unprivileged runtime; APIs/importer use Python slim with build dependencies removed from runtime.
2. Implement Nginx same-origin proxy, SPA deep-link routing, compressed static assets, public-route allowlist, blocked internals, security headers, global rate limits and request-ID replacement.
3. Complete Compose project `stellar-atlas-dev`: PostgreSQL named volume, one API each, web host port 8080, one-shot role/bootstrap/migration/import commands, health-gated startup. Development can mount source only in an explicit dev profile; the release-like profile runs built images.
4. Keep the catalog archive outside source-control/build context except the deliberate importer COPY from a checksum-verified staged asset. Do not copy `.local/secrets` through a broad context.
5. Complete `dev-up`, `dev-down`, `images-build`, `smoke` and `doctor` diagnostics. A second dev-up is safe; dev-down does not remove volumes.
6. Test on a fresh Compose volume, then repeat startup, recreate API/web containers and restart database; saved shared journeys and catalog survive. Test service outage messages through the gateway.
7. Confirm public routing blocks `/metrics`, `/openapi.json`, `/docs`, internal positions/import/migration and unknown API prefixes, while local/internal maintenance still works.

**Exit:** one documented command launches the release-like local app, idempotent startup works, no unintended host ports are published.

### P10 — Finish automated tests and security policy

**Depends on:** P09. **Output:** executable CI checks before repository protection.

1. Organize unit/contract/integration/browser tests and fixtures; provide one host action with checked exit codes. Use actual PostgreSQL integration tests and a fixture catalog for CI speed.
2. Implement generated-contract drift check, ID-string/binary golden tests, importer atomicity tests and API failure tests. Frontend Vitest covers state/formatting; Playwright covers real gateway journeys and mobile/list fallback.
3. Install/configure Gitleaks, Bandit, npm audit, pip-audit, Syft, Grype and Checkov at locked versions. Add scanner provenance checks and normalized report output. No blanket scanner suppression.
4. Implement project-specific IaC assertions for public ports, limits/probes, non-root runtime, no wildcard app permissions, no embedded secrets, and image digests in demo manifests. Local/CI test-image exceptions are limited to the documented overlay and `ci-<40hexsha>` tags.
5. Create safe detector fixtures excluded from shipped sources and actual secret scans; self-test that the scanners reject those fixtures. Fake secret values must be obvious fixtures and never real tokens.
6. Implement gate/exception-expiry parser, scanner DB-age policy and failure summaries. Start exception file empty; add findings only with specific rationale/expiry if an unavoidable platform issue is encountered.
7. Add test coverage minimum 85% for unit/ID/import/calculation modules, 75% for backend business logic; frontend coverage focuses on URL/state/error logic rather than renderer implementation details. No meaningless snapshot/count tests solely to inflate coverage.
8. Implement `test`/`security` actions so a failed required tool/test exits nonzero. Run the complete suite once against release-like Compose and capture actual results.

**Exit:** positive checks pass; safe negative detector tests prove the gates block; no promised check is a placeholder script returning success.

### P11 — Validate release images, provenance, and artifact policy

**Depends on:** P10. **Output:** locally verified images and release-generation scripts.

1. Implement image builder with source SHA, build timestamp, data snapshot, license and OCI source labels. Handle a dirty tree by refusing a release build; local dev builds may use explicit `dev-dirty` metadata.
2. Build each image once, scan the built local image, generate SPDX JSON via Syft, and save local digest/image-ID evidence. Check image layers/files for credentials, `.env`, caches, raw unrelated workspace data and build-only tooling.
3. Run non-root/read-only smoke tests for each runtime. Verify Python shared package/migrations are included and importer can run from its image without the repository mounted.
4. Implement render-release script: accepts only schema-validated image digests and version metadata, renders demo manifests deterministically, and fails if any application image/tag or source SHA is inconsistent.
5. Define the deploy-branch generated tree and previous-release metadata. Add tests that an invalid digest, unknown namespace, Secret object, privileged pod or cluster-scoped app object cannot be promoted.
6. Add publication/signature code paths for later trusted GitHub jobs; local checks use test keys only and cannot be mistaken for trusted GitHub OIDC signatures.
7. Cap ordinary workflow report artifacts at 20 MiB/run and 3-day retention; upload traces/screenshots only on failure, sanitized and bounded. Keep data in release assets and images in GHCR, not the shared free Actions artifact allowance. Cleanup action removes expired project artifacts with an audited log.

**Exit:** all four release-like images pass local security/behavior checks; deterministic rendering and artifact budget checks pass. Registry publication/signing remain explicitly unrun until P15/P17.

### P12 — Build the local cluster and Terraform platform

**Depends on:** P11. **Output:** reproducible cluster, real network isolation, persistent database.

1. Implement the pinned kind configuration, loopback-only API/NodePort mapping, CIDR-overlap detection and cluster-name/context guard. If `stellar-atlas-demo` exists, inspect its node image/config and reuse only on exact match; otherwise require the guarded backup/rebuild action.
2. Vendor Calico 3.33.0 `calico.yaml`, record its raw SHA-256/license, and apply a committed Kustomize patch: pool CIDR matches kind, IPIP disabled, VXLAN enabled, networking backend/readiness consistent with VXLAN. Do not fetch moving latest manifests during bootstrap.
3. Create cluster without waiting for ready CNI-dependent nodes, install Calico, then wait up to 300 s for Calico DaemonSet/controllers, CoreDNS and node Ready. Check DNS and pod-to-pod HTTP with pinned fixture images. If it fails, collect events/logs and correct the exact kernel/config problem; never continue with a non-enforcing replacement CNI.
4. Split Terraform into **two roots**: `infra/terraform/foundation/` (namespaces, RBAC, quotas, policies, PVCs) and `infra/terraform/runtime/` (PostgreSQL and monitoring). Store separate local state files under `.local/terraform/`; runtime reads foundation outputs locally. This overrides the flat grouping shown in the layout example and avoids waiting on database Secrets before their namespace exists.
5. Configure Kubernetes provider with the explicit `kind-stellar-atlas-demo` context and pinned kubectl/CA config; no cloud provider/backend. Ignore state, saved plans and machine tfvars. Add prevent_destroy to critical PVC resources. Serialize Terraform runs with a host lock file; back up local state before apply.
6. Run fmt/validate/plan on foundation and inspect the exact resource list. Apply namespaces, restricted app/data policies, scoped roles, quotas and PVC claims. Use kind's `standard` local-path storage class, not an invented static PV or Windows NTFS database mount.
7. Apply generated Secrets after foundation namespaces exist using `cluster-secrets`. API/Job credentials stay in the application namespace; PostgreSQL's admin secret stays in the data namespace. Grafana credentials stay in monitoring.
8. Apply runtime with monitoring disabled initially, creating `postgres-0`, internal Service and 10 GiB PVC; mount PGDATA in a subdirectory writable by documented UID/GID/fsGroup. Wait for pg_isready. Bootstrap both databases/roles through binary-safe protected stdin and reapply exact grants.
9. Run a second plan in both roots; expect zero changes. Test Terraform drift using a harmless project-owned namespace label, show the plan detects it, and restore by apply. Never use a real secret value as the drift example.
10. Verify NetworkPolicies behavior with allowed/denied test labels and database credentials. Test denied pod cannot reach PostgreSQL or APIs, and permitted service routes still work. Save connect-timeout and permission-denied evidence.
11. Verify PostgreSQL recreation using the same PVC preserves a fixture row; do not delete the PVC/cluster for this test. Confirm database and Kubernetes API have no public/host listener beyond the explicit loopback administration context.
12. Complete `cluster-create`, `platform-plan`, `platform-apply`, `cluster-secrets` and diagnostics. Capture actual cluster resource usage.

**Exit:** node/network healthy, policies demonstrably enforce, PostgreSQL persists across pod replacement, Terraform replan is empty, no cloud resources created.

### P13 — Deploy and validate the application in Kubernetes locally

**Depends on:** P12. **Output:** working application through the intended Kubernetes gateway.

1. Create base and demo Kustomize templates with section 3 resource/security/probe defaults, labels and service accounts. Application Services use ClusterIP except web NodePort. No application Service exposes 5432/admin/metrics externally.
2. Create local bootstrap overlay using locally built `dev-<source-sha>` images with imagePullPolicy Never. This overlay is only for pre-GitOps/local tests; the demo overlay accepts digests only. Load images into the exact kind cluster explicitly.
3. Apply catalog/journey migration Jobs and wait for success; then importer with sealed baseline; then runtime ConfigMaps/Services/Deployments. Verify readiness and exact source/data metadata. Bound Jobs and make their failure logs available without secret values.
4. Configure API/web writable emptyDirs, runtime UIDs, graceful shutdown and healthy startup. Read-only errors must be fixed through specific writable mounts, not disabling the filesystem restriction.
5. Open `http://127.0.0.1:8080`; run real-data browser smoke: default count 1151, Proxima long-ID selection, full profile, independent distance calculation, shared journey create/open, saved-local flow and list fallback.
6. Run cluster-internal HTTP/DB isolation tests using the same labels/policies as final Jobs. Confirm internal positions works from Journey and is blocked at the gateway.
7. Delete one Catalog pod and measure replacement/readiness while the second pod answers requests. Record request failures rather than claiming zero downtime without measurement.
8. Complete `demo-bootstrap` and local `smoke`. Keep Argo disabled until P17 so manual bootstrap resources are not fighting a reconciler.

**Exit:** the actual Kubernetes app works at loopback port 8080 with baseline data and runtime restrictions.

### P14 — Add monitoring, backup scheduling, and restore verification

**Depends on:** P13. **Output:** observable and recoverable deployment.

1. Enable Terraform-owned monitoring manifests: Prometheus, Grafana and kube-state-metrics with fixed digests, resource limits, private Services and explicit RBAC. Add 2 GiB Prometheus and 1 GiB Grafana PVCs, protected from routine destruction. Do not deploy an operator/Helm chart.
2. Configure pod discovery/scrapes, normalized metrics and alerts from section 3.7. Disable Grafana analytics, update checks, anonymous access and plugin downloads. Generate/protect its admin password; datasource is internal Prometheus.
3. Provision the committed dashboard JSON and datasource automatically. Verify both replicas produce distinct scrape series, and dashboard queries show actual requests/errors/restarts and source/data versions. Avoid high-cardinality ID labels.
4. Implement local-only admin port-forward helpers for Grafana 3000, Prometheus 9090, Argo 8081; bind explicitly to 127.0.0.1 and record owned processes. Never expose these through the public gateway/tunnel.
5. Implement `backup` to dump both DBs to temporary host files using subprocess bytes, hash, verify pg_restore list, add snapshot/release metadata, then rename to a completed timestamp directory. Complete the seven-backup retention/path guards.
6. Implement the host backup scheduler (Python stdlib background process) which runs on demo-start and every 30 min. Launch hidden on Windows, record project identity/heartbeat and use a project-owned stop-request file. Never kill a PID solely because an old PID file matches; confirm ownership. Stop waits for an in-progress dump to finish.
7. Implement `restore --target restore-check`: create isolated namespace/PostgreSQL/PVC with no public Service, restore with fresh credentials/grants, verify complete catalog counts/chunks and a saved journey, compare checksums/results, then remove only the explicitly named test resources after evidence is saved.
8. Write RUNBOOK sections for monitoring, backup validity, restore-check, and restricted manual inspection. Test a corrupt/truncated dump is rejected before any demo database change.

**Exit:** dashboards show real traffic, a complete host backup exists, restore-check and corruption rejection pass; scheduled backup lifecycle is tested.

### P15 — Create the free remote repository, data release, and CI

**Depends on:** P14. **Output:** public source/data distribution and enforced quality/security gates.

1. Re-run local test/security/history scans and inspect staged files before the first push. Verify ownership/publication target and account free-plan settings from P00. Do not upload `.local`, secrets, raw catalog or private evidence.
2. Create or safely connect the public `stellar-atlas` repository, set `origin` to the authenticated owner's actual URL, and push the complete bootstrap source. Creation/push are implementation actions; do not pretend writing this plan already did them.
3. Publish the P03 data release with verified asset/notice files; confirm anonymous download returns the expected bytes/hash. Update and commit the resolved data URL/archive hash in its lock manifest.
4. Implement `ci.yml` job IDs `quality` and `security`, explicitly named `ci / quality` and `ci / security`, so those exact check-run names can be required. Confirm actual check-run names through GitHub before enabling the rule. Trigger on all PRs to main and main pushes; do not path-skip a required check into a permanently pending state. Use standard `ubuntu-24.04` hosted runners, pinned actions and Node/Python versions.
5. Quality runs frozen installs, lint/typecheck, unit/contracts, PostgreSQL integration, frontend tests and Playwright against release-like Compose with the small fixture. Security runs all policy checks and scanner self-tests. Build all Dockerfiles on PRs without pushing, signing or accessing secrets.
6. Add a bounded ephemeral kind+Calico cluster job for server-side schema validation and network-policy/runtime smoke using the fixture/local `ci-<sha>` images. Omit Argo/monitoring from this ephemeral test; those are verified on the actual host. Keep one API replica in CI to fit free-runner resources. Always delete only the CI cluster on cleanup.
7. Cache dependency/scanner downloads with keys including lock hashes and DB timestamps. Do not share a credentialed Docker config with untrusted PR jobs. Do not upload secrets in artifacts or run `pull_request_target` on checkout of contributor code.
8. Configure bounded artifact upload/cleanup and report retention. Keep total retained Actions artifact usage below 400 MiB; if it approaches this threshold, delete oldest project reports after archiving essential sanitized evidence, never buy extra storage.
9. After the first successful CI run, enable main branch protection/ruleset with the two exact required checks, PR requirement, up-to-date checks, no force push/deletion, no paid feature. Add CODEOWNERS using actual maintainer login. Keep deployment branch separate from these checks.
10. Configure Dependabot weekly for npm, Python requirements and GitHub Actions; updates create PRs and do not auto-merge or auto-deploy failed checks. Pin generated updates before merge.
11. Prove a wrong unit-conversion test in an isolated PR fails quality and blocks merge, then fix it. Prove insecure config fixture in a separate isolated PR fails security. Do not merge intentionally failing branches or publish unsafe images.
12. Implement release workflow shell/Python scripts, but set repository variable `GITOPS_ENABLED=false` for the explicit first-publication bootstrap. The release can build/scan/sign/publish/promote its deploy snapshot now, but the verification job reports `bootstrap: deployment not yet verified` and cannot claim a deployed release.
13. On first GHCR publication, explicitly change each of the four packages to public in its package settings, retaining repository association. Public repo does not automatically guarantee public packages. Verify anonymous image manifest/pull for all four digests before P17.

**Exit:** public source/data are accessible; protected main checks genuinely enforce; release artifacts are publicly pullable and signed; first deployment verification remains explicitly pending until GitOps starts.

### P16 — Establish the public HTTPS endpoint

**Depends on:** P15 and healthy local app. **Output:** verified external access with no cloud compute.

1. Verify local gateway smoke and confirm only it is bound at 127.0.0.1:8080. Check no public mapping was added for DB, Kubernetes API, Grafana, Prometheus or Argo.
2. Start the pinned `cloudflared tunnel --url http://127.0.0.1:8080` as a hidden project-owned process using argument arrays and explicit executable/log paths. Record process ownership and do not replace unrelated tunnels. No account, token or named-tunnel configuration is needed.
3. Parse the actual assigned HTTPS `trycloudflare.com` URL from the owned process output; verify origin routing and record its temporary lifetime. No domain/account purchase. A generated URL alone is not an external application smoke pass.
4. Store public origin in `.local/operator.json` and GitHub repository variable `PUBLIC_BASE_URL`; validate it is HTTPS and the recorded `.trycloudflare.com` hostname. Never interpolate unchecked URL text into a shell command.
5. Run an external smoke from a standard GitHub runner or a phone on mobile data. Verify TLS, frontend deep links, API metadata, star search, estimate and shared journey open. Visitors must not need authentication or a tunnel client.
6. Probe forbidden paths/ports through the public origin; show 404/403, not proxied admin content. Recheck HTTP error formatting/security headers and rate-limit response.
7. Complete public-start/stop and host demo-start/stop actions: verify prerequisites, start existing kind node containers/Docker services if permitted, wait on readiness, start/verify tunnel, start backup scheduler, and show URL/version summary. Stopping closes the tunnel and scheduler and stops only owned project containers; it does not delete PVCs/cluster/state.
8. Record exact operating instructions and uptime limits in About/RUNBOOK. Each new Quick Tunnel has a different hostname; update the repository variable, operator state and assessment link before the next release/demo. Never claim a stopped tunnel's former URL remains usable.

**Exit:** external user can use the Kubernetes application over HTTPS; no admin surface is exposed; correct public URL and limitations are documented.

### P17 — Enable GitOps and finish the first verified deployment

**Depends on:** P16 and published release images/deploy ref from P15. **Output:** normal Git-driven CD without bootstrap loopholes.

1. Verify deploy ref contains only the generated application tree/release metadata and all four digests are anonymous-pullable, scanned and correctly signed. Verify current rendered manifests with policy/schema checks.
2. Vendor Argo 3.5.5 namespace-install manifest and separate CRDs; record checksums/license. Bootstrap CRDs using server-side apply with no blanket force-conflicts, wait for Established, then apply namespace-scoped components and explicit same-cluster controller RoleBinding.
3. Install AppProject/Application from section 3.6 pointing to `https://github.com/<owner>/stellar-atlas.git`, revision `deploy`, path `application`, destination `stellar-atlas`. No credentials are needed to read a public repo. Do not enable Argo to manage Terraform platform resources.
4. Complete Argo component resource bounds/disabled unused components, local-only UI access, generated admin credential, reconciliation polling and sync options. Use can-i tests to prove allowed Deployment/Job access and denied Secret/Namespace/ClusterRole management.
5. Let Argo adopt the existing bootstrap application objects and reconcile them to digest-pinned demo manifests. This intentionally replaces local Never-pull image settings. Wait for migration/import Jobs, runtime rollout, Synced+Healthy and PostSync smoke.
6. Compare running images and frontend/API source/data metadata to release.json, not just a green Argo badge. Run external smoke again and verify shared records/data survived adoption.
7. Set `GITOPS_ENABLED=true` permanently after this verified bootstrap. A release workflow must fail/pending rather than silently skip deployment checks if the variable/URL is missing afterward. Add a CI assertion that release-ready documentation/config does not leave bootstrap mode enabled.
8. Commit/update evidence with actual sync revision, running pod imageIDs, source SHA, catalog version, signature checks and public test result. Complete gitops-bootstrap command and ownership documentation.

**Exit:** actual GitOps deployment is Synced/Healthy, application is externally verified, bootstrap mode is disabled, no direct runner-to-cluster access exists.

### P18 — Prove the full release pipeline and Git rollback

**Depends on:** P17. **Output:** end-to-end automated delivery and recovery evidence.

1. Implement release workflow exactly as section 3.4: trusted main CI result, stale-commit guard, serial release concurrency, build once, SBOM/scan, push exact images, obtain digests, keyless sign+verify, render/policy-check, fast-forward deploy commit, and external verification.
2. External verifier polls every 10 s for at most 600 s, with per-request timeout 5 s. It checks `/version.json`, both `/v1/meta`, required active snapshot/count, estimate oracle and shared journey round-trip. All three source SHAs must equal the promoted commit. Use a unique idempotency UUID for each test create.
3. Distinguish outcomes: verified release; reachable old release after rollout deadline; candidate reachable but smoke fails; entirely unreachable host. Store status and reason in workflow summary/release evidence. A successful image push cannot satisfy deployment status.
4. For reachable-old/candidate-bad failures, restore the prior deploy application tree through a new commit **only if deploy head is still the candidate promoted by this run**, then verify the previous source SHA. For entirely unreachable host, do not blindly mutate Git; fail/pending with host-start instructions. If the cluster first appeared offline then resumes, rerun verification before retrying/rebuilding.
5. Implement `rollback.yml` workflow_dispatch accepting a previously recorded release ID, not arbitrary shell/manifest input. Verify its signatures/digests, compatibility floor and no-destructive-migration rule, render that saved release, commit on deploy with compare-and-swap guard and verify public metadata. Source main remains unchanged.
6. Make a real small visible application change (About wording/release badge), open PR, pass checks, merge, and observe automated public update. Record the PR, CI run, images, deploy commit, Argo revision and public SHA as one chain.
7. In the demo environment, promote a controlled non-security failure candidate that fails readiness/smoke while preserving old healthy replicas. Record timeout/recovery behavior; restore through Git. Use a dedicated explicit demo switch in a test-only overlay/workflow input, not a latent public application endpoint or permanent production fault toggle.
8. Demonstrate concurrent/stale release protection with two queued safe commits; final deployed release must be the newest approved source, never a stale job winning a race. Test rollback head-change guard refuses to overwrite a later release.
9. Keep DB schemas forward-compatible; rollback only app images/config and active snapshot pointer if explicitly part of the saved release. Do not revert PostgreSQL volume contents or Alembic version automatically.

**Exit:** one normal change deploys automatically and is verified; one failed release is recovered through Git; concurrency guards and offline-host reporting pass.

### P19 — Complete DevSecOps and runtime attack-surface demonstrations

**Depends on:** P18. **Output:** evidence for security throughout the lifecycle.

1. Run Gitleaks over complete main/deploy history and runtime build contexts. Verify only protected local files/ephemeral GitHub tokens hold credentials; no Kubeconfig or DB secret is present in GitHub variables/artifacts/images.
2. Capture dependency/image/IaC/SAST reports and DB ages for a successful release. Verify all four Cosign identities/digests and SBOM references. Show unsigned/wrong-identity digest cannot pass promotion validation; do not weaken verification to broad identity regex.
3. Demonstrate fake-secret detector rejection and unsafe Kubernetes manifest rejection in isolated local fixtures/PRs, then corrected passing checks. Do not publish a real secret or known vulnerable application image.
4. In cluster, verify app runs non-root/read-only without service-account tokens; privileged/root/missing-limit app manifests are rejected by policy checks/Pod Security. Prove CNI-specific exceptions do not extend to app namespaces.
5. Verify actual allowed/denied network connections, DB role grants, public-route denial, body bounds, invalid JSON, rate limits, same-origin behavior, XSS-safe object labels and no outbound astronomy calls.
6. Test malicious inputs: >2^53 ID preservation, path traversal chunk IDs, SQL meta-characters in q, 1000-item position batch, Infinity speed, user-supplied remote URL/redirect, and huge view fragment. Expect bounded 4xx/no crash/no external fetch.
7. Inspect logs and reports for credentials/personal headers; ensure normalized route metrics do not create series per source ID/journey UUID. Keep the app unauthenticated by design; do not imply public share UUIDs are private accounts.
8. Audit zero paid services, purchases, nonstandard runners, storage overages, data-LFS use and expired security exceptions. Record original-software/data/tool license notices.

**Exit:** all mandatory gates and runtime protections have evidence; exceptions are specific, justified and unexpired; no secret-containing evidence is published.

### P20 — Prove Kubernetes operations and data failure handling

**Depends on:** P19. **Output:** measured operational demonstrations.

1. Delete one Catalog pod and one Journey pod separately; watch ready replica count, requests, replacement time and restart/event evidence. Expect <120 s on the warmed reference host; investigate if exceeded.
2. Change Journey replicas from 2 to 3 through source/template PR and release (or a recorded GitOps-only approved scale revision), observe reconciliation, request distribution and quota usage, then return to 2 through Git. Do not run an unrecorded kubectl scale against Argo self-heal.
3. Demonstrate rolling application update and previous-image Git rollback with continuous read probes. Record any failures; do not claim HA across a host loss.
4. Temporarily stop Catalog while keeping Journey running. Existing frozen shared summaries remain readable; estimates return controlled 503; Journey liveness stays healthy. Restore Catalog and show recovery without manual API restart.
5. Run malformed catalog import (wrong checksum/duplicate/invalid coordinate) as a bounded Job. Verify failure log/report and unchanged active data/count/chunk hashes. Repeat the valid snapshot to show idempotence.
6. Demonstrate an intentionally interrupted staging import leaves old active data intact, then a valid new transform/version candidate can activate atomically. For a demonstration version, change only a verified alias/provenance transformation version; do not fabricate astronomical coordinates. Retain both immutable snapshots.
7. Stop/start the named node container and public tunnel after a fresh backup; verify PVC data, Argo reconciliation and public app return. Record the downtime/operating-hours constraint.
8. Test host offline during release: workflow cannot report verified success; when the host returns, Argo reconciles approved Git state and a rerun verifies actual SHA. Record this separately from application rollback failure.

**Exit:** pod recovery, Git-managed scaling, rolling delivery, dependency failure, atomic data handling and host-resume behavior are demonstrated.

### P21 — Complete backup, restore, rebuild, and safe teardown

**Depends on:** P20. **Output:** repeatable disaster recovery and cleanup.

1. Take a fresh complete host backup with both dumps, dataset/release references and checksums. Create a known shared journey and include its UUID/result in the backup verification fixture.
2. Restore into isolated restore-check target, compare all snapshot/star/chunk counts/hashes and sampled calculations, prove saved journey survives, and measure duration. Verify regenerated roles/grants/credentials work.
3. Implement/run guarded `cluster-rebuild --confirm-cluster stellar-atlas-demo` only after fresh backup verification: close public access and scheduler; stop GitOps; archive Terraform states; delete only the named kind cluster; retain host backups/source/tools. Do not bypass prevent_destroy or run a blanket Terraform destroy against persistent claims. Cluster deletion bypasses Kubernetes lifecycle protections, which is why the host backup/explicit-name gate is mandatory.
4. Recreate exact kind+Calico/foundation, generate credentials, restore PostgreSQL with fresh owner/grants, restore catalog/journey data, recreate monitoring, reinstall restricted Argo, reconcile saved release, then restart/verify public tunnel. Do not import a new snapshot over the restored active one accidentally.
5. Handle local Terraform state from the deleted cluster explicitly: archive it, initialize fresh project state for the new cluster, and reapply; do not treat old state as proof resources still exist. Never remove unrelated state or force-unlock a lock owned by a running operation.
6. Verify real public source/data SHA, shared journey and local browser saved-item behavior after rebuild; collect actual RTO. Restore-check resources are separately removed using explicit target names.
7. Test `demo-stop`/`demo-start` twice for idempotency without data deletion. Default teardown is a safe stop retaining cluster/PVC/state. Its explicit `--remove-cluster --confirm-cluster stellar-atlas-demo` form requires a verified fresh host backup, removes only that named cluster, then archives its state; it never wipes host backups or unrelated Docker volumes. Test teardown dry-run prints exact names/paths; reject unexpected cluster names, root paths and paths outside `.local`.
8. Write precise RUNBOOK recovery branches: Docker not running/access denied; wrong context; port conflict; DNS/CNI failure; ImagePullBackOff/private GHCR; PodSecurity/read-only mount failure; DB auth/migration; Argo RBAC/CRD; missing snapshot; scanner DB unavailable; disk full; lost tunnel; stale Git release and invalid dump.
9. For final assessment leave the agreed demo environment running or stopped according to the user's instruction; never teardown merely because documentation is complete. State operational status honestly.

**Exit:** complete cluster reconstruction and restored data are proven; safe stop/start and scoped teardown work; backups remain outside the cluster.

### P22 — Finish performance, visual, accessibility, and reproducibility acceptance

**Depends on:** P21. **Output:** final measured acceptance, not aspirational targets.

1. Measure default 50-ly initial interaction time and compressed payload; verify exact 1151 count and no raw CSV transfer. Measure 100-pc view with exact 300526 median-in-scope objects. Preserve all records; do not silently downsample to pass a visual test.
2. Run 30-second camera-orbit FPS measurement on the declared host/browser, record median/p95 frame time/DPR/count and GPU/software-rendering status. Default radius must meet NF04. Use shader point cloud, label cap, Worker picking and DPR bound as the prescribed remedies.
3. Benchmark local read+estimate endpoints with ten concurrent virtual clients and a total paced arrival rate of 8 requests/s for 60 s (6 read/s, 1 estimate/s, 1 other read/s). Exclude shared-create from the main load test; separately verify create limits. This avoids mistaking intentional global rate limiting for an API reliability failure. Record errors/429s/latency distribution and warm-up conditions.
4. Compare localhost and public tunnel timings separately. Quick Tunnel throughput/availability limits cannot be represented as a backend benchmark. If public transfer is slow, verify chunk compression/cache/progressive loading rather than adding paid hosting.
5. Review desktop 1440×900/1920×1080 and mobile 390×844, keyboard-only use, reduced motion, color legend correctness, text contrast, profile overflow, no-WebGL fallback, deep-link refresh and saved-item limits. Capture final actual screenshots, not generated mockups.
6. Test default/empty/maximum radius, lost network mid-fetch, old snapshot share, expired/purged journey, localStorage denied/full, WebGL context loss and malformed fragments. Ensure retry/cancellation does not produce stale selection/calculation.
7. Test a clean clone in a separate workspace with no original node_modules/venvs/cache/secrets. Follow README commands, download sealed asset, create fresh fixture Compose environment and validate locks. An existing team machine may additionally execute the same bootstrap; do not claim a second physical-host test if only a clean local clone was used.
8. Re-run the appropriate full suite and security gates after fixes. Record measured values and remaining blockers without changing acceptance targets silently. Any required failure keeps final acceptance incomplete.

**Exit:** FR/NF acceptance has actual results; visual/interactive behavior is reviewed; clean-clone instructions work.

### P23 — Package assessment evidence, release, and implementing-agent handoff

**Depends on:** all previous phases. **Output:** submission-ready project and reproducible operational handoff.

1. Complete `docs/ARCHITECTURE.md` with service, data, runtime, trust-boundary and delivery diagrams matching the implementation. Include resource ownership and the distinction between Compose dev, ephemeral CI and local demo.
2. Complete `docs/RUNBOOK.md` with exact commands from clean setup to demo-start/stop, routine release, data operation, rollback, backup/restore, local-only admin access, public URL maintenance, resource/billing inspection, and guarded teardown.
3. Complete `docs/EVIDENCE_MATRIX.md`: each DV topic maps to source files, actual command/run URL, screenshot/report and a one-sentence explanation of what it proves. Map FR/NF criteria to tests/measurements in ACCEPTANCE.md.
4. Create `evidence/manifest.json` referencing actual commit IDs, PRs, workflow runs, image digests, signatures/SBOMs, deployment revisions, cluster/policy demonstrations, data validation, public URL checks and recovery/performance results. Small sanitized summaries may enter Git; bulky/raw/private material remains local or in bounded release assets.
5. Write a 12–15 minute `docs/DEMO_SCRIPT.md`: public product tour; service/image separation; IaC no-change/drift; PR security/test rejection; approved release/version; Argo reconciliation; pod recovery/scaling; dashboards; Git rollback; backup/restore evidence; zero-cost and uptime limits. Use recorded recovery evidence if a live destructive demonstration would exceed assessment time.
6. Run a final cost audit: free Personal/educational plans, standard public runners, current registry policy, bounded artifacts, no paid domains/cloud, no AWS resources. Attach sanitized dates/links; free-provider policy is periodically rechecked, not guaranteed forever.
7. Reconcile deployed release to final tested source, tag software `v1.0.0`, publish release notes/data credits/known operational limits and sanitized evidence assets. Tagging alone cannot replace CI/CD acceptance. Do not overwrite the immutable data release.
8. Run final external smoke and all relevant acceptance checks against that exact release. Record final public URL and its expected operating schedule, latest backup path/hash, current deployment SHA and unresolved **actual** blockers if any.
9. Ensure no acceptance item says passed merely because a command was planned. If any required item is failed/blocked/not run, mark project incomplete and state the precise requirement; do not omit it from the final handoff.
10. Provide the user a concise completion report linking PRD, implementation/runbook, repository/release, public URL, evidence matrix and actual test results. State whether the local demo is running. Preserve originals and approved scope.

**Exit:** every required FR/NF/DV item has evidence; a new implementing/operating agent can reproduce and operate the result without inventing omitted architecture or deployment steps.

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
| `PUBLIC_BASE_URL` | Actual HTTPS tunnel URL; GitHub repository variable and ignored operator config | Release verifier/runbook, not baked browser code |
| `GITOPS_ENABLED` | false only during P15 bootstrap; true after P17 | Trusted release workflow |
| `PGDATA` | `/var/lib/postgresql/data/pgdata` on Linux PVC | PostgreSQL |
| `EXPECTED_SIGNER` | Exact verified release-workflow certificate identity, no wildcard | Promotion/rollback verification |

Web API calls use relative `/api/...` URLs and share links use `window.location.origin`, so a tunnel change does not require rebuilding frontend code. Serve static build `/version.json` with SOURCE_SHA; serve nonsecret `/release.json` from a read-only mounted release ConfigMap containing source SHA, RELEASE_ID, image digests, and dataset ID. Release verification checks both static source identity and this runtime deployment identity.

API metadata includes both `source_sha` and `release_id`. This distinguishes deploying the same images in a retry, controlled fault demonstration, or rollback. No health/readiness metadata is accepted solely from an unauthenticated client request header.

### 5.2 Release manifest, retry, rollback, and expiry semantics

`release.json` required fields:

```json
{
  "schema_version": 1,
  "release_id": "generated-from-actual-run",
  "source_sha": "actual-full-commit",
  "source_repository": "actual-owner/stellar-atlas",
  "created_at": "actual-UTC-timestamp",
  "dataset": {"snapshot_id": "locked-id", "raw_sha256": "locked-hash", "fixture": false},
  "images": {
    "web": {"ref": "ghcr.io/owner/stellar-atlas-web@sha256:actual", "sbom_sha256": "actual"},
    "catalog": {"ref": "ghcr.io/owner/stellar-atlas-catalog@sha256:actual", "sbom_sha256": "actual"},
    "journey": {"ref": "ghcr.io/owner/stellar-atlas-journey@sha256:actual", "sbom_sha256": "actual"},
    "importer": {"ref": "ghcr.io/owner/stellar-atlas-importer@sha256:actual", "sbom_sha256": "actual"}
  },
  "signer_identity": "exact-expected-workflow-identity",
  "compatibility": {"catalog_schema": 1, "journey_schema": 1, "model": "constant-speed-v1"},
  "verification": {"state": "pending"}
}
```

The example uses descriptive values; production schema validation requires real SHAs/digests/URLs and rejects those strings. Verified status is emitted by the verifier as a separate report; it must not be set to verified merely when this manifest is generated.

For a source SHA already built, reuse the complete verified four-image set and archived SBOMs; rescan it with the current allowed vulnerability DB before promotion. Do not overwrite existing immutable `sha-<fullsha>` image tags or rebuild with a different base under the same source release. If only a partial set was published, recover the missing verified build outputs or create a new source commit/build-set ID; never mix unverified sets. Retries get a new runtime RELEASE_ID while preserving image digests.

Capture the complete prior application tree before promotion, not just a previous SHA string. Store its exact manifest tree and release metadata as a bounded software-release asset and in deploy-branch history. Retain all assessment release manifests/digests until course completion. The rollback workflow selects only this recorded set and checks schema compatibility; it never executes arbitrary paths supplied by workflow input.

After app rollback, re-run the import Job with its release-declared snapshot and `--activate`; an already-ready older snapshot can become active again without reimporting rows. Schemas remain at the forward-compatible head; frozen shared journey values remain readable. Do not equate image rollback with database restoration.

The controlled fault demo uses a temporary, test-only manifest overlay with a deliberately nonexistent **readiness path**, unchanged verified images and a new RELEASE_ID. It leaves liveness/process behavior intact and old healthy replicas running. Restrict this workflow input to explicit maintainer dispatch and restore the previous Git tree after observation; it is never a public application feature or a normal release default. The verifier detects that candidate RELEASE_ID did not become healthy, even if source SHA was unchanged.

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

# P21: explicit destructive recovery demonstration, only after a verified backup
.\ops.ps1 cluster-rebuild --confirm-cluster stellar-atlas-demo
.\ops.ps1 smoke --target public
```

The dispatcher accepts the shown arguments as its API; implement validation and useful `--help`, not a set of shell snippets requiring the operator to infer missing flags. If PowerShell execution policy blocks a local script, use the equivalent `python tools/run.py ...` action; do not weaken machine-wide policy.

P15's first release is allowed to report artifact publication plus pending bootstrap verification, but the final delivered workflow must have GitOps enabled and must not pass a deployed status without public verification. P16 needs a local app, not an already-working Argo instance; P17 needs the already-published deploy ref. This order avoids a circular bootstrap dependency.

### 5.4 CI fixture and production separation

- CI fixtures have their own manifest/count and `fixture=true`. CI Playwright expected counts derive from that manifest; production acceptance uses the exact baseline counts from the PRD.
- The release builder rejects APP_ENV demo + fixture=true. Promotion schema rejects a fixture dataset. The full importer image is built only from the checksum-verified public data-release archive.
- Local CI images use explicit CI/bootstrap tags only inside their documented overlays. The deployed demo uses image digests and complete signature evidence.
- CI uses software-rendered Chromium for functional tests; no CI FPS result can be advertised as the reference laptop's hardware result.
- Full real-data validation runs before data publication and on every release build; PR tests use fixtures and cannot claim to have validated an arbitrary new catalog upload.

### 5.5 Failure decisions

| Condition | Required response |
|---|---|
| Docker/WSL query denied only in sandbox | Repeat normal-session prerequisite probe; report access boundary; no speculative reinstall. |
| Host has insufficient resources | Use another existing team machine with this exact configuration; otherwise report a concrete prerequisite failure. No paid replacement. |
| Existing exact GitHub repo/cluster contains unrelated work | Preserve it and report the identity collision; never replace silently. |
| Snapshot checksum changes | Treat as a new candidate/version; retain sealed baseline; never edit expected hash merely to pass. |
| Optional alias/photometry absent | Display ID/Not available; preserve correct coordinates and feature behavior. |
| Required coordinates/unit/schema invalid | Reject candidate; keep active snapshot and prior report. |
| Scanner unavailable/DB too old | Fail release gate with retry/cache-age diagnostics; do not skip scan. |
| GHCR package private | Make the four intended public packages public after inspecting their contents; reverify anonymously; no cluster PAT workaround. |
| No public tunnel route | Verify pinned cloudflared, local gateway health, owned process/logs, outbound connectivity and the current Quick Tunnel URL. Record any external-service blocker; no cloud purchase or silent hosting change. |
| Public app unreachable during release | Report pending/failed verification and host-start instructions; do not claim deployed or blindly overwrite deploy history. |
| Candidate unhealthy while old route remains reachable | Compare-and-swap restore prior deploy tree, verify prior RELEASE_ID and record failure. |
| Newer deploy commit exists during rollback | Abort stale rollback; do not force push or revert someone else's newer release. |
| PVC/node lost | Verify external host dumps, rebuild exact project cluster and restore; never claim local PVC alone is a backup. |
| Policy objects exist but connections are not denied | Fail network-policy acceptance; repair CNI/enforcement before continuing. |
| Public bandwidth slow | Optimize verified chunks/cache/loading; report tunnel timing separately. |
| Free-provider terms change | Recheck whether the already-approved free option remains usable; use local equivalents/declared tunnel contingency, report any unmet public-delivery requirement, never authorize spending. |

## 6. Requirements-to-phase and evidence traceability

| Requirement | Implement | Final verify/evidence |
|---|---|---|
| FR01–FR04 atlas/layers/selection | P05, P06, P08 | P13 real-data UI, P22 rendering/counts/screenshots |
| FR05–FR07 search/profiles/neighbors | P03, P06, P08 | P10 contracts/browser, P22 null/alias/neighbor checks |
| FR08 distance | P02, P07, P08 | Independent triangle and real-object calculation tests |
| FR09–FR11 journeys/playback/sharing | P07, P08 | P10 browser/API, P18 public shared round-trip |
| FR12 share views | P08 | URL round-trip, bad fragment, old snapshot tests in P22 |
| FR13 saved items | P08 | Browser storage/dedup/cap/fallback tests in P22 |
| FR14 observer | P08 | Coordinate-basis test and actual viewpoint demonstration P22 |
| FR15–FR17 resilience/release/accessibility | P08, P09 | P18 release metadata, P22 fault/mobile/keyboard/reduced motion |
| NF01 zero cost | P00, P15, P16 | P19/P23 dated cost/configuration audit |
| NF02 reproducibility | P01, P09, P12 | P21 rebuild, P22 clean clone |
| NF03–NF06 performance/transfer | P05, P06, P08 | P22 measured local/public reports |
| NF07 security | P04, P09, P10, P12 | P19 gates/ports/grants/runtime/policy proof |
| NF08 recovery | P12, P17, P18 | P20 pod/rollback timing |
| NF09 atomic data | P05 | P20 invalid/interrupted/valid candidate evidence |
| NF10 persistence | P04, P12, P14 | P21 restore/rebuild with saved journey |
| NF11 expiry | P07, P13 | Controlled-clock/retention tests in P10/P22 |
| NF12 availability | P16 | P20 offline/resume; About/runbook/public schedule |
| DV01 microservices | P04, P06, P07, P13 | Service HTTP trace, separate images/deployments and privilege isolation |
| DV02 Docker | P09, P11 | Fresh Compose, non-root/read-only images, digests/SBOM |
| DV03 IaC | P12 | First apply, zero-diff replan, label drift repair and rebuild |
| DV04 Kubernetes | P12, P13 | P20 probes/recovery/scaling/rollout; policy proof |
| DV05 CI/CD | P15, P17, P18 | PR gates → image provenance → deploy commit → Argo → public release |
| DV06 DevSecOps | P10, P11, P19 | Negative gate examples, verified image signatures and runtime restrictions |
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

### Planning-document completion check

- PRD defines 17 functional, 12 nonfunctional and 8 DevOps acceptance requirements.
- Implementation phases P00–P23 cover initial prerequisites through final operational handoff, each with dependencies, ordered actions and exit criteria.
- External/machine inputs have acquisition rules; no paid fallback is permitted.
- Data source, schemas, units, binary format, APIs, runtime topology, ownership, workflow privileges, bootstrap ordering, rollback, backup and acceptance evidence are specified.
- No application code, installation, cloud resource, Git repository publication or deployment has been executed by this document-writing task.

