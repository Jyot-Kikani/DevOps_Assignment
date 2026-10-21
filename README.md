# Stellar Atlas

A nearby-star atlas and zero-cost DevOps course project. Catalog and Journey
run as separate services on local Kubernetes. Delivery, security, recovery
and demonstrable operations are the priority. The product specification is in
[PRD](docs/PRD.md); execute the [implementation plan](docs/IMPLEMENTATION_PLAN.md)
in order and consult [acceptance status](docs/ACCEPTANCE.md) for actual progress.

## Prerequisites

For a DevOps-focused walkthrough, open the standalone
[interactive architecture visualiser](docs/architecture_visualiser.html) in a browser,
read the [architecture and file guide](docs/architecture_guide.md), and use the
[demonstration script and talking points](docs/demo_guide.md).

Windows, Python 3.13, Git, Docker Desktop with Linux containers/WSL2, at least
16 GiB RAM/4 logical CPUs/40 GiB free disk. Use existing hardware only. P00's
reference host and actual checks are recorded in docs/P00_PREREQUISITES.md.
GitHub Free and account-level zero paid-usage budgets were reviewed. The source
repository is the existing `Jyot-Kikani/DevOps_Assignment`. Basic GitHub CI runs
before P04. The user made this repository public on 2026-10-20;
`main` requires PRs and both passing CI checks, including for admins.
Batch 5 adds data/image distribution, GitOps and a temporary HTTPS app route;
see its report for actual verification and the current URL.
No AWS, purchased domain, paid hosting or expiring credit is required.

## Bootstrap

Run from a normal PowerShell terminal in the clone:

```powershell
python tools/run.py tools-lock --verify-only --json
python tools/run.py tools-lock --json
python tools/setup_envs.py
python tools/run.py doctor --json
```

The first command verifies committed lock bytes without installing anything.
The second restores exact project-local Windows tools from official URLs; it
does not upgrade versions or edit global PATH. The third installs third-party
dependencies only from hashed locks into `.local/venvs/{catalog,journey,importer,ops}`.
The host command package itself uses only the Python standard library.
Linux runtime and Windows development requirements are locked separately.

`doctor` exits nonzero when prerequisites are missing or access is denied.
Docker/WSL/CIM failures confined to a sandbox do not imply broken installations;
rerun in the normal terminal. GitHub credentials may be reused from Git Credential
Manager in a child process only; login/MFA remains with the human. Billing evidence
and actual operator configuration stay local. A clean clone must review its own
account evidence; it cannot inherit another checkout's credentials or readiness.

Copy `tools/operator.example.json` into ignored `.local/operator.json` and supply
the authenticated personal owner and local paths. The repository name is
`DevOps_Assignment`; preserve existing contents/history and `origin`. Do not create
a new `stellar-atlas` repository. See ADR 0004 for early CI, the public visibility
decision and protected-main rules. `PUBLIC_BASE_URL` is null until the Kubernetes app's
Quick Tunnel exists. No auth key or tunnel account is required.

## Commands and phase boundary

`./ops.ps1 <action>` dispatches to the same Python interface using argument arrays.
If local PowerShell script execution is restricted, invoke Python directly.
Both entry points resolve the repository from their script path. Use `--help`
for available actions. Actions appear only when implemented; there are no success
stubs for future deployment or security checks.

Frontend scripts are in `apps/web/package.json`. With the pinned Node directory
on the current process PATH, use `npm.cmd --prefix apps/web run build`, `typecheck`,
`lint`, `test`, `test:e2e`, or `dev`. Tests without implemented cases must fail;
frontend build/tooling checks alone do not establish application acceptance.
Batch 3 now provides the real atlas and complete local Compose application.

After installing the locked Python environments, build/install the first-party
packages with `python tools/build_packages.py`. With the pinned Node directory
on the process PATH, restore both npm graphs using `npm.cmd ci --ignore-scripts
--engine-strict --no-audit --no-fund --cache=.local/npm-cache --prefix apps/web`
and the same command with `--prefix tools/codegen`.
Run `python tools/run.py contracts --check --json` to check generated schemas/types,
or omit `--check` to regenerate. `python tools/run.py test --json` runs the implemented
unit/contract/frontend gates and records their exact scope; it does not claim
database, deployment or browser E2E acceptance.

P04 adds a database-only Compose profile, protected local credentials, explicit
bootstrap/migrations and real PostgreSQL checks. Run those commands in your normal
Windows account, as described in [P04 databases](docs/P04_DATABASES.md). The database
has no host port; `db-stop` preserves its volume. The required CI quality job also
runs the database integration suite.

Batch 2 implements P04–P07 only: [atomic importer](docs/P05_IMPORT.md),
[Catalog API](docs/P06_CATALOG.md) and [Journey API](docs/P07_JOURNEYS.md).
Run `python tools/run.py db-check --json` for mandatory fixture-backed PostgreSQL
and real service HTTP tests; add `--full` for the preserved sealed catalog and
the real-object journey oracle. Missing databases/dependencies fail the check.
`python tools/run.py catalog-import --json` verifies/reuses and activates the sealed
baseline after tests; `catalog-report` reads its current state. All these database
commands run in the normal user session. Detailed results are in
[the Batch 2 report](docs/BATCH2_REPORT.md). Batch 3 adds the application described below.

## Data and evidence

Preserve `validation/` and `design/mockups/`. The existing validation scripts
download/overwrite outputs: inspect them before running. Original CSV/bin files
stay ignored; normalized archives, environments, credentials, state, backups,
reports and publication staging stay under `.local/`. Small attributed fixtures
and sanitized evidence may be committed. Mockups are visual references, never
astronomical coordinate input.

Software licensing is MIT for original code; Gaia/GCNS data retains its upstream
license and attribution. See [data notice](data/LICENSE-NOTICE.md).

P03 operations: `python tools/run.py data-seal --json` verifies and seals the
existing baseline; `python tools/run.py data-publish --json` stages the immutable
release locally. The full-data check is
`.local/venvs/ops/Scripts/python.exe tools/check_sealed_data.py` (Windows).
See [sealed data and publication scope](docs/P03_DATA.md). P15 now provides the
verified public data release; the local staging/sealing checks alone make no
public-access claim. See [publication](docs/P15_PUBLICATION.md).

## Early GitHub CI

Use only [Jyot-Kikani/DevOps_Assignment](https://github.com/Jyot-Kikani/DevOps_Assignment).
Its existing `origin` is preserved; public visibility was explicitly chosen by the user.
Protected `main` requires an up-to-date PR and `ci / quality` plus `ci / security`;
no second-person approval is mandatory. The early workflow runs
on main pushes, PRs targeting main, and manual dispatch. It checks implemented
quality gates and full-history secrets/publication exclusions. It does not deploy
or publish data/images. See [CI scope and Batch 2 handoff](docs/EARLY_CI.md).

Future implementation follows the [course-scope amendment](docs/adr/0005-course-assignment-scope.md): focused checks and simple DevOps demonstrations. Advanced hardening is optional; existing CI and completed backend checks stay intact.

## Batch 3 local application (P08–P11)

```powershell
python tools/run.py dev-up --json
# Open http://127.0.0.1:8080/explore
python tools/run.py smoke --target local --json
python tools/run.py dev-down --json
```

Explore, Journeys, Saved and About use the real Catalog/Journey APIs. The atlas
uses measured positions; saves are local to the browser and shares last 30 days.
The gateway is loopback-only. Stop preserves PostgreSQL data. No Kubernetes,
public tunnel, image/data publication or paid service is started by these commands.

See [Batch 3 report](docs/BATCH3_REPORT.md), [web](docs/P08_WEB.md),
[Compose](docs/P09_COMPOSE.md), [focused checks](docs/P10_CHECKS.md) and
[local release images](docs/P11_RELEASE_IMAGES.md). `images-build` requires a
clean commit; `dev-up --no-build` reuses its exact prepared local image set.

**Known image-security limitation:** pinned Grype scans complete but the strict
high-severity gate still fails on base-image findings, even after the documented
runtime update. This is not a clean-scan release. No findings are hidden and no
image was published in Batch 3. Batch 5 publishes scanned images under ADR 0005
with the strict failures preserved; review [the actual findings](docs/P10_IMAGE_REVIEW.md).
Existing required CI checks remain intact.
Batch 4 adds the local Kubernetes platform, deployment and recovery demonstration below.

## Batch 4 local Kubernetes (P12–P14)

After the existing bootstrap and clean-source image preparation, run in your normal
Windows session. Stop the Stellar Atlas Compose gateway first to free port 8080:

```powershell
python tools/run.py dev-down --json
python tools/run.py cluster-create --json
python tools/run.py platform-apply --root foundation --json
python tools/run.py cluster-secrets --json
python tools/run.py platform-apply --root runtime --json
python tools/run.py demo-bootstrap --json
python tools/run.py monitoring-up --json
python tools/run.py monitoring-check --json
python tools/run.py backup --json
python tools/run.py restore --target restore-check --json
```

Open `http://127.0.0.1:8080/explore`. The app uses the prepared real-data image
digests and separate PostgreSQL roles. Both Terraform roots keep state under
ignored `.local/terraform`; credentials are applied outside Terraform. Monitoring
is private, accessible through loopback port-forwards. Restore uses a unique
temporary target and preserves the working database and host backups.

See [Batch 4 results](docs/BATCH4_REPORT.md), [P12 platform](docs/P12_KUBERNETES.md),
[P13 deployment](docs/P13_LOCAL_DEPLOYMENT.md) and [P14 monitoring/recovery](docs/P14_MONITORING_RECOVERY.md).
Routine node stop/start preserves the PVC; cluster deletion can destroy it.
Do not start Compose while kind owns 8080. Existing Grype findings remain recorded
in Batch 3; new release scans retain their actual threshold results.

## Batch 5 public delivery (P15–P18)

The trusted successful-main release workflow builds/scans/publishes four GHCR
images, verifies anonymous access and writes digest manifests to `deploy`.
The frozen data assets are distributed through the canonical repository release.
Publication alone does not establish a working deployment.

```powershell
python tools/run.py public-start --json
python tools/run.py smoke --target public --json
python tools/run.py platform-apply --root foundation --json
python tools/run.py gitops-bootstrap --json
python tools/run.py gitops-check --json
# Stop the current temporary public route when finished:
python tools/run.py public-stop --json
```

See [publication](docs/P15_PUBLICATION.md), [public access](docs/P16_PUBLIC_DEMO.md),
[Argo](docs/P17_GITOPS.md) and [update/rollback](docs/P18_UPDATE_ROLLBACK.md).
The tunnel URL changes on restart and works only while this host, Docker, kind,
cloudflared and internet are available. Argo/UI/monitoring/database remain private.
After Argo takes application ownership, use Git deploy commits for updates;
do not reapply the earlier manual bootstrap overlay. P19 is a separate batch.

See [Batch 5 results](docs/BATCH5_REPORT.md) for the current temporary URL,
external-device confirmation, published versions and update/rollback evidence.
Database backups now record the running release, including a GitOps rollback,
rather than an older local Compose image record.

## Batch 6 operations (P19–P21)

Use the retained, initialized GitOps cluster for routine demonstrations:

```powershell
python tools/run.py demo-start --json
python tools/run.py pod-replace --json
python tools/run.py demo-stop --json
```

Safe stop retains the exact kind node container and PVC, records a catalog/journey
checkpoint and stops only the project's recorded tunnel. Start verifies persisted
data and Argo, resuming a previously active tunnel with a new temporary URL.
`demo-start --local-only` skips opening a tunnel. It does not create a missing
cluster; first-time setup follows the earlier guides. Preserve host backups.

See [security evidence](docs/P19_SECURITY_SUMMARY.md),
[pod replacement/scaling](docs/P20_KUBERNETES_OPERATIONS.md), the short
[operating/recovery guide](docs/P21_OPERATIONS.md) and [Batch 6 results](docs/BATCH6_REPORT.md).
The strict Grype threshold remains failed. P22/P23 final review is recorded below.

## Final course submission (P22–P23)

Start with [the submission and demo script](docs/P23_SUBMISSION.md),
[final review](docs/P22_FINAL_REVIEW.md), [acceptance register](docs/ACCEPTANCE.md)
and [Batch 7 report](docs/BATCH7_REPORT.md). The submission includes the architecture,
course-topic evidence table, operating/recovery links, selected actual screenshots,
measurements and remaining limitations. Use the Batch 7 runtime record for the
current temporary public URL and running source; earlier reports are checkpoints.

P22 verifies 1,151 objects at 50 ly and 300,526 at exactly 100 pc, desktop/mobile
flows, keyboard selection, view links, Saved and representative fallback/retry
states. Mobile is viewport emulation and Chromium uses software rendering; no
formal accessibility/FPS/load certification is claimed. Existing scientific,
transfer, retention, deployment and recovery evidence is reused where unchanged.
The strict image-scan failures remain documented. No additional infrastructure
is required for assessment; routine operation follows [P21](docs/P21_OPERATIONS.md).
