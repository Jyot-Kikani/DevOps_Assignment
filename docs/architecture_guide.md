# DevOps architecture and file guide

Start with [the interactive architecture visualiser](architecture_visualiser.html),
then use [the demo guide](demo_guide.md) to present the implementation.
Open the HTML file directly in a browser; it needs no server or internet.
This guide describes the completed P00–P23 implementation inspected on
21 October 2026. Runtime checks establish what is running today;
[Batch 7](BATCH7_REPORT.md) records the final implementation checkpoint.

Current backend topology: [six-service map](SIX_SERVICES.md). Journey calls
Calculation → Catalog; Search, Atlas Map and Snapshot are independent read APIs.
Shared read libraries and data access are described in ADR 0006. See Batch 9 for
actual deployment status; earlier batch reports describe the original release.

## 1. The architecture in one explanation

“I use GitHub to review and test changes, Docker to package them, GHCR to
distribute exact images, Terraform to define the local platform, and Argo CD
to deploy the application from Git. Kubernetes keeps the requested pods
running. Prometheus and Grafana show their behavior. Host-side database dumps
provide a separate recovery copy. Cloudflare exposes only the application
through a temporary HTTPS route.”

```text
SOURCE / DELIVERY — hosted GitHub, no laptop kubeconfig in Actions
codex/* → PR → ci / quality + ci / security → protected main
                                                   ↓ successful main CI
                  verified data → build eight images → Grype → GHCR digests
                                                              ↓
                              deploy branch: app/app.json + release + scan record
                                                              ↓ pull / reconcile
LOCAL PLATFORM — Docker Desktop → single kind node              Argo CD
    Terraform foundation → namespaces, PVC, Argo namespace RBAC     ↓
    Terraform runtime    → PostgreSQL + private monitoring      application
    local operator       → Secrets and Argo installation/bootstrap ↓
    public browser → Cloudflare Quick Tunnel → loopback :8080 → Web NodePort
                                                              ↓
                                            private app Services / pods
                                                              ↓
                                               PostgreSQL → 10 GiB PVC
    API /metrics → Prometheus → Grafana             ↓ manual pg_dump
                                       ignored host backups → isolated restore
```

The source branch `main` and delivery branch `deploy` have different jobs.
`main` contains human-maintained source/configuration; `deploy` contains generated
application manifests and release evidence. Argo watches **`deploy`, path `app`**.
It does not watch `deploy/local` on main or run the GitHub build pipeline.

## 2. Who owns what?

| Owner | Actual responsibility | Main file / control |
|---|---|---|
| kind, invoked by the host helper | Creates the single Kubernetes node as a Docker container and loopback mappings | [`infra/kind/cluster.yaml`](../infra/kind/cluster.yaml) |
| Terraform foundation | Four namespaces, PostgreSQL PVC, namespace-scoped Argo permissions | [`foundation/main.tf.json`](../infra/terraform/foundation/main.tf.json), [`gitops.tf.json`](../infra/terraform/foundation/gitops.tf.json) |
| Terraform runtime | PostgreSQL Deployment/Service and optional enabled Prometheus/Grafana resources | [`runtime/main.tf.json`](../infra/terraform/runtime/main.tf.json) |
| Local operator helpers | Private credentials, explicit bootstrap/migration/import Jobs, pinned Argo install and Application setup | [`kubernetes.py`](../tools/stellar_ops/kubernetes.py), [`delivery.py`](../tools/stellar_ops/delivery.py) |
| GitHub Actions | Checks source, builds/scans/publishes images, writes generated deploy branch | [`ci.yml`](../.github/workflows/ci.yml), [`release.yml`](../.github/workflows/release.yml), [`release.py`](../tools/release.py) |
| Argo CD | Reconciles application Deployments, Services, ConfigMaps and retention CronJob from Git | [`application.json`](../infra/argocd/application.json), [`project.json`](../infra/argocd/project.json) |
| Kubernetes controllers | Maintain replica count, replace pods and execute Jobs/CronJobs | Rendered application resources on `deploy` |
| Human operator | Reviews findings, verifies live deployment, takes backups, starts/stops the demo | [`tools/run.py`](../tools/run.py), [P21](P21_OPERATIONS.md) |

Keeping these owners separate avoids two controllers overwriting the same
resources. After Argo takes ownership, application changes go through Git.
`demo-bootstrap` is an earlier setup operation, not the routine restart command.

## 3. Repository map: where to look and why

### Entry points, reproducibility and private local files

| File / directory | Purpose and DevOps concept |
|---|---|
| [`README.md`](../README.md) | Setup entry point, prerequisites, operational commands and links to phase evidence. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md), [`AGENTS.md`](../AGENTS.md) | Branch/PR rules, required checks, course scope and evidence discipline. |
| [`ops.ps1`](../ops.ps1) → [`tools/run.py`](../tools/run.py) → [`cli.py`](../tools/stellar_ops/cli.py) | PowerShell wrapper → Python entry point → strict command dispatcher. Same operations through either interface; unavailable actions have no success stubs. |
| [`tools/toolchain.lock.json`](../tools/toolchain.lock.json) | Frozen executable versions, downloads and checksums. Locking makes the toolchain repeatable; it does not make it vulnerability-free. |
| [`tools/locks/`](../tools/locks/) | Hashed Python dependencies, Terraform/provider and vendor tool inputs; Windows and Linux dependencies are distinguished. Some locks are preparatory and do not prove those tools are used. |
| [`apps/web/package-lock.json`](../apps/web/package-lock.json), [`tools/codegen/package-lock.json`](../tools/codegen/package-lock.json) | Exact npm dependency graphs for application and contract generation. |
| [`tools/setup_envs.py`](../tools/setup_envs.py), [`tools/build_packages.py`](../tools/build_packages.py) | Recreate isolated Python environments and build/install the project's own wheels. |
| [`tools/operator.example.json`](../tools/operator.example.json), [`.env.example`](../.env.example) | Committed examples; actual operator configuration is local. |
| [`.gitignore`](../.gitignore), [`.dockerignore`](../.dockerignore) | Prevent private/generated state entering Git or unnecessary build contexts. Neither replaces secret scanning or review. |
| `.local/` — ignored, host-specific | Tools, environments, operator settings, credentials, kubeconfig, Terraform state/plans, reports, release records, backup dumps and tunnel state. A clone does not contain a working deployment or these private files. |

Do not display `.local/secrets`, kubeconfig, operator credentials or Terraform
state during a demonstration. The fact that a tool or vendored manifest exists
does not establish that it is installed. In particular, Calico, signing/SBOM
enforcement and additional scanner stacks are not part of the demonstrated scope.

### CI, image packaging and publication

| File | What it actually does |
|---|---|
| [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) | PR/main/manual CI. `ci / quality` verifies locks, restores dependencies, checks contracts/tests/web, runs real PostgreSQL integration and two browser flows, and builds eight images without publication. `ci / security` verifies locks/pinned actions and runs full-history secret/publication checks. |
| [`tools/stellar_ops/quality.py`](../tools/stellar_ops/quality.py), [`tools/check_web_ci.py`](../tools/check_web_ci.py) | Implement quality checks and fixture-backed API/browser CI. CI uses disposable credentials and a small attributed data fixture, not the laptop's full dataset. |
| [`tools/ci_security.py`](../tools/ci_security.py) | Full-history Gitleaks and publication exclusion checks. This is what the required security job runs; a green check is not a clean image scan. |
| [`.github/workflows/release.yml`](../.github/workflows/release.yml) | Trusted successful-main CI triggers publication; manual main dispatch is also supported. Uses narrowly scoped write permissions, serializes releases, retains release/scan artifacts for three days. |
| [`tools/release.py`](../tools/release.py) | Verifies latest main/checks, downloads checksum-verified data, builds/scans eight images, pushes GHCR images, verifies anonymous digest access and writes `deploy`. Scanner execution errors abort; recorded severity-threshold failures are retained under ADR 0005's reviewed-publication policy. |
| [`apps/web/Dockerfile`](../apps/web/Dockerfile) | Multi-stage asset build → non-root Nginx gateway runtime, pinned bases, revision label and health check. |
| [`services/catalog/Dockerfile`](../services/catalog/Dockerfile), [`services/journey/Dockerfile`](../services/journey/Dockerfile) | Separate non-root API images with pinned bases, hashed dependency installation, revision labels and health checks. |
| [`jobs/importer/Dockerfile`](../jobs/importer/Dockerfile) | Importer image: controlled data/bootstrap job tooling. CI's build-only importer context is not a published real-data image. |
| [`tools/stellar_ops/application.py`](../tools/stellar_ops/application.py) | Local Compose lifecycle and image preparation/checking; earlier local release metadata. |
| [`tools/stellar_ops/security.py`](../tools/stellar_ops/security.py) | Local secret-control demonstration and Grype image scans, including a fake-token rejection generated only in process memory. |
| [`contracts/`](../contracts/), [`tests/`](../tests/) | Versioned interface/release contracts and executable quality evidence. Prevent contract drift and catch integration failures before delivery. |

Protected `main` requires an up-to-date PR and both required jobs, including for
admins. The publisher does not get local cluster credentials. It writes Git;
local Argo pulls desired state and Kubernetes pulls images from GHCR.

**Three identities to explain:** source SHA identifies the code; image digest
identifies the packaged bytes; deploy commit identifies the desired resource set.
They are different identifiers. `gitops-check` and smoke tests connect them to
the actual running application. A registry push alone cannot prove deployment.

Documentation-only commits under `docs/` and the existing README/contribution/
agent guidance allowlist preserve the current deployment. A manual release
dispatch can explicitly republish. See the condition in `tools/release.py`.

### Kubernetes, Terraform and GitOps

| File / directory | Purpose and distinction |
|---|---|
| [`compose.yml`](../compose.yml), [`compose.database.yml`](../compose.database.yml) | Earlier local development/integration environment: services, health ordering, one-shot jobs, private secret files and persistent database volume. Compose and kind share host gateway port 8080; run one demonstration path at a time. |
| [`infra/kind/cluster.yaml`](../infra/kind/cluster.yaml) | One pinned kind node; Kubernetes API on loopback; NodePort 30080 mapped to host `127.0.0.1:8080`. The laptop is the server. |
| [`infra/terraform/foundation/`](../infra/terraform/foundation/) | Namespaces, 10 GiB ReadWriteOnce PVC with `prevent_destroy`, application namespace Role/RoleBinding for Argo. |
| [`infra/terraform/runtime/`](../infra/terraform/runtime/) | PostgreSQL and optional enabled monitoring. PostgreSQL uses a **Deployment**, with Recreate strategy; this project does not use a database StatefulSet. |
| Both roots' `versions.tf` and `.terraform.lock.hcl` | Provider/backend requirements and provider integrity locks. `*.tf.json` is native Terraform configuration, not generated Kubernetes YAML. |
| [`tools/stellar_ops/kubernetes.py`](../tools/stellar_ops/kubernetes.py) | Explicit project kubeconfig/context, Terraform plan/apply, secret injection, ordered Jobs, monitoring checks, host backup and isolated restore. State is kept under `.local/terraform/<root>`. |
| [`deploy/local/app.json`](../deploy/local/app.json) | Source template for app Deployments/Services, release ConfigMap mount and daily retention CronJob. Includes digest placeholders, probes, resources and runtime security settings; it is not the Argo watched path. The release/bootstrap helper creates the ConfigMap itself. |
| [`deploy/local/jobs.json`](../deploy/local/jobs.json) | Ordered bootstrap → Catalog migration → Journey migration → importer Jobs. Job failure stops initial rollout. |
| [`infra/argocd/application.json`](../infra/argocd/application.json) | Repository, `deploy` revision, `app` directory and destination; automated sync with prune/self-heal. |
| [`infra/argocd/project.json`](../infra/argocd/project.json) | Restricts accepted repository, namespace and resource kinds. No cluster-wide resource allowlist. |
| [`infra/terraform/foundation/gitops.tf.json`](../infra/terraform/foundation/gitops.tf.json) | Namespace-scoped Kubernetes RBAC matching the application's management needs. AppProject restrictions and Kubernetes RBAC are separate controls. |
| [`tools/render_argo.py`](../tools/render_argo.py), [`infra/vendor/argocd/`](../infra/vendor/argocd/) | Renders the pinned Argo installation/resource inclusions. Vendored bytes are verified; unused components are omitted. |
| [`tools/stellar_ops/delivery.py`](../tools/stellar_ops/delivery.py) | Public tunnel start/stop, GitOps bootstrap/check, live release identity/digest verification and smoke checks. |
| [`tools/stellar_ops/operations.py`](../tools/stellar_ops/operations.py) | Retained-node start/stop checkpoints and targeted Journey pod replacement, with persistence verification. |

These files are on the **separate `deploy` branch**, not missing from main:

| Generated file | Purpose |
|---|---|
| `app/app.json` | Concrete digest-pinned application resources Argo applies. |
| `release.json` | Source/release/data identity and all eight published image references. |
| `scan-summary.json` | Grype version, threshold, actual exit codes and severity counts. |

Inspect them in the [deploy branch](https://github.com/Jyot-Kikani/DevOps_Assignment/tree/deploy).
Scaling edits this branch's **Journey Deployment replicas**. A normal Git revert
on current deploy provides rollback. `kubectl scale` and `rollout undo` conflict
with Argo self-heal and are not the documented update path.

### Visibility, access, persistence and recovery

| File / directory | DevOps role |
|---|---|
| [`monitoring/prometheus.json`](../monitoring/prometheus.json) | Scrapes both internal API `/metrics` endpoints every five seconds. |
| [`monitoring/datasources.json`](../monitoring/datasources.json), [`monitoring/dashboards.json`](../monitoring/dashboards.json) | Provision Grafana's Prometheus datasource and dashboard discovery. |
| [`monitoring/stellar-atlas-dashboard.json`](../monitoring/stellar-atlas-dashboard.json) | Four panels: availability, request totals/status, p95 duration and database failures. These are observed metrics, not uptime or load guarantees. |
| [`apps/web/nginx.conf`](../apps/web/nginx.conf) | Gateway allowlist, health route, release identity route, request limits and public 404s for private/admin routes. |
| [`tools/stellar_ops/secrets.py`](../tools/stellar_ops/secrets.py), [`db.py`](../tools/stellar_ops/db.py) | Generate/reuse protected local credentials and orchestrate separate database roles, bootstrap/migrations and integration checks. |
| [`tools/stellar_ops/data.py`](../tools/stellar_ops/data.py), [`data/`](../data/) | Immutable data checksums/provenance and attributed release distribution. Relevant here as artifact integrity, not astronomy. |
| `.local/backups/<timestamp>/` — ignored | Two custom-format PostgreSQL dumps plus manifest/checksums, actual release identity and recovery sample. Located outside the kind node. |
| `.local/public/state.json` — ignored | Current temporary tunnel state/URL; old report hostnames are historical. |
| `.local/reports/` — ignored | Actual command outputs, monitoring/pod/restart/restore results and detailed evidence. Inspect relevant reports without exposing secrets. |
| [`docs/evidence/`](evidence/), [`BATCH4_REPORT.md`](BATCH4_REPORT.md)–[`BATCH7_REPORT.md`](BATCH7_REPORT.md) | Concise committed evidence and dated results. Historical measurements are not fresh observations. |
| [`docs/adr/0005-course-assignment-scope.md`](adr/0005-course-assignment-scope.md), [`ACCEPTANCE.md`](ACCEPTANCE.md) | Authoritative course scope and implemented/evidence status. Older plans can contain optional, unimplemented hardening. |
| [`validation/`](../validation/), [`design/mockups/`](../design/mockups/) | Preserved original references; not routine DevOps commands. Validation downloaders can overwrite outputs, so do not rerun them for this demo. |

## 4. Concepts using this project's concrete behavior

| Concept | Project example / faculty explanation |
|---|---|
| CI vs CD | CI tests source in disposable runners; publication builds distributable artifacts and Git desired state; Argo reconciles the local deployment. |
| Image vs container vs pod | Dockerfile builds an image; kind's Kubernetes runs containers inside pods from that image digest. The kind node itself is a Docker container. |
| Deployment vs Service | Deployment maintains replicas; Service gives stable routing despite a pod UID/IP changing. |
| Readiness vs liveness | Readiness controls whether a pod receives traffic; liveness can restart an unhealthy container. A successful probe is narrower than an end-to-end smoke test. |
| Job vs CronJob | Initial migration/import Jobs finish; the Journey retention CronJob schedules periodic cleanup. Neither is an always-running API Deployment. |
| ConfigMap vs Secret | Release/configuration metadata is ordinary configuration; credentials are separate private Secret inputs. Kubernetes Secrets are not automatically an encrypted vault. |
| IaC and drift | Terraform compares declared platform state against real resources; the recorded label-change exercise detected and repaired drift. Argo performs a separate application reconciliation loop. |
| Persistence vs backup | PVC survives pod replacement and retained-node restart; host dump supports recovery after loss of node storage. Neither means multi-host availability. |
| Rollback vs restore | Revert app desired state to older digests; restore data into an isolated target to verify recovery. Application rollback leaves the live database/schema in place. |
| Metrics vs logs | Prometheus stores numeric time series; Grafana queries them. This project has no centralized ELK/Loki log stack or alerting suite. |
| Scale vs HA | Two Journey replicas demonstrate replication on the same node. Both still depend on the same laptop. |

## 5. What to edit for a change

| Intended change | Start here | Delivery / verification |
|---|---|---|
| Change CI gates | `.github/workflows/ci.yml`, corresponding helper/test | Source PR; both existing required job names preserved. |
| Change base image or dependency | Relevant Dockerfile + dependency/tool lock workflow | Source PR, build/scan/review; a pin is not a patch by itself. |
| Change app probes, limits or persistent app configuration | `deploy/local/app.json` source template | Source PR → release renders new `deploy/app/app.json` → Argo → `gitops-check`. |
| Demonstrate temporary replica count | Current **deploy** branch `app/app.json` | Follow [P20](P20_KUBERNETES_OPERATIONS.md); normal commit/push, verify 2/2, revert your change to 1/1. |
| Change a platform resource | Relevant Terraform root | Plan/review/apply with host helper; Argo does not apply Terraform changes. |
| Change dashboard | `monitoring/*.json` | Review runtime Terraform plan/apply; provisioned configuration checksum causes pod rollout; `monitoring-check`. |
| Roll back application | Current deploy history | Revert exactly the intended deploy commit and verify; follow [P18](P18_UPDATE_ROLLBACK.md). |
| Refresh public hostname | No committed configuration edit | `public-stop`, `public-start`, public smoke; copy the new URL. |

## 6. Claims to keep precise

- **Grype strict threshold failed.** Batch 7 records exit 2 for all four images.
  Passing secret/quality CI and permitted publication do not change that result.
  Use the selected release's `scan-summary.json` for counts; advisories change.
- One host, one kind node, no cloud Kubernetes, no HA/24×7 promise. Cloudflare
  supplies a temporary route; it does not host the workloads.
- Database, Kubernetes administration, Argo and monitoring are private.
  Loopback forwards are temporary local access, not public deployment.
- Monitoring history is ephemeral; backups/restores are manual. The isolated
  restore proves data recovery, not an automatic full application rebuild.
- Routine start checks an existing installation. The final clean-clone check
  verified source/locks/CLI, not a second fully provisioned runtime.

Read next: [demo guide](demo_guide.md), [P21 operations](P21_OPERATIONS.md),
[P14 monitoring/recovery](P14_MONITORING_RECOVERY.md), [final report](BATCH7_REPORT.md).
