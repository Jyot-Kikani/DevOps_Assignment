# Stellar Atlas

A nearby-star atlas and zero-cost DevOps course project. Catalog and Journey
will run as separate services on local Kubernetes. Delivery, security, recovery
and demonstrable operations are the priority. The product specification is in
[PRD](docs/PRD.md); execute the [implementation plan](docs/IMPLEMENTATION_PLAN.md)
in order and consult [acceptance status](docs/ACCEPTANCE.md) for actual progress.

## Prerequisites

Windows, Python 3.13, Git, Docker Desktop with Linux containers/WSL2, at least
16 GiB RAM/4 logical CPUs/40 GiB free disk. Use existing hardware only. P00's
reference host and actual checks are recorded in docs/P00_PREREQUISITES.md.
GitHub Free and account-level zero paid-usage budgets were reviewed. The source
repository is the existing `Jyot-Kikani/DevOps_Assignment`. Basic GitHub CI runs
before P04. The user made this repository public on 2026-10-20;
`main` requires PRs and both passing CI checks, including for admins.
Data/image distribution and the temporary HTTPS app URL remain later gates.
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
frontend build/tooling checks do not establish a usable atlas. Dockerfiles,
Compose, database persistence and running services belong to later phases.

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
See [sealed data and publication scope](docs/P03_DATA.md). Actual GitHub release
publication is deferred to P15; no public URL is claimed by these local checks.

## Early GitHub CI

Use only [Jyot-Kikani/DevOps_Assignment](https://github.com/Jyot-Kikani/DevOps_Assignment).
Its existing `origin` is preserved; public visibility was explicitly chosen by the user.
Protected `main` requires an up-to-date PR and `ci / quality` plus `ci / security`;
no second-person approval is mandatory. The early workflow runs
on main pushes, PRs targeting main, and manual dispatch. It checks implemented
quality gates and full-history secrets/publication exclusions. It does not deploy
or publish data/images. See [CI scope and Batch 2 handoff](docs/EARLY_CI.md).
