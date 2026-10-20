# Early CI and Batch 2 handoff

The user authorized this checkpoint after P03 on 2026-10-20. It changes delivery
sequence and repository identity, leaving P04–P07 for another chat.

Use only [Jyot-Kikani/DevOps_Assignment](https://github.com/Jyot-Kikani/DevOps_Assignment),
existing `origin`. Its inspected state was an empty private repository with working
personal-owner authentication, admin permission and Actions enabled. The user then
made this same repository public on 2026-10-20; live verification confirmed it.
Preserve this public choice and account-level zero paid-usage hard stops. No new repository,
account, paid runner, cache/artifact upload or deployment is part of this checkpoint.

`.github/workflows/ci.yml` runs on all main pushes and PRs to main, and manual
dispatch. There are no path filters. Concurrent obsolete runs are cancelled;
quality timeout is 15 minutes, security timeout 5 minutes. Jobs use standard
Ubuntu 24.04, SHA-pinned actions, read-only contents permission and checkout with
persisted credentials disabled. Python is 3.13.5; Node is 24.22.0. Dependency locks
are verified before installation; no moving version selection or remote caching.

| Exact check name | Implemented scope |
|---|---|
| `ci / quality` | Hashed Linux dependency installs into four isolated environments; dependency consistency; first-party wheel build/install; npm frozen installs; schema/TypeScript drift; unit and contract tests; frontend tests, typecheck, lint and build |
| `ci / security` | Committed lock integrity; action SHA allowlist; complete Git-history raw/private-file exclusion policy; checksum/version-pinned Gitleaks full-history scan |

Local validation passed 54 Python tests and 3 frontend tests, plus the
quality/build/drift/lock/security checks. The original full catalog resealed to
the same archive SHA-256. The existing FastAPI test client emits one nonblocking
HTTPX deprecation warning. Actual hosted-run evidence is separate: see
[GitHub Actions](https://github.com/Jyot-Kikani/DevOps_Assignment/actions) and ignored
`.local/reports/early-ci-github.json`. Local results alone do not prove a hosted run.

No artifacts or caches are uploaded by this initial workflow. Standard hosted
runner execution is free for this public repository. Artifact/cache limits and
reviewed zero-budget hard stops remain unchanged. Report actual rights/quota
failures; never change account visibility/budgets to bypass them.
Current billing rules: [GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

This early scope is not the complete P10/P15 security/integration suite. Database
integration, browser E2E, dependency/SAST/image/IaC scans, detector self-tests,
coverage gates, full P15 enforcement demonstrations, data/image publication,
signing, delivery and public app verification remain in their phases. The initial
private-repository protection request returned HTTP 403. After the user made the
repository public, free protection was applied and read back successfully:

- `main` requires PRs and both named checks from GitHub Actions, with the branch up to date.
- Rules include admins; force pushes and branch deletion are disabled.
- Conversations must be resolved; mandatory human approval count is zero.

The API request uses `checks` only; combining it with legacy `contexts` was rejected
with HTTP 422. Correcting the request format retained all intended rules. Saved
readback: ignored `.local/reports/main-protection.json`.

Hosted verification caught a Linux `Text file busy` error in the first main-push
run during concurrent `venv.EnvBuilder` creation. `tools/setup_envs.py` now prepares
environments sequentially instead of starting four creators together. Frozen
dependencies, hash checks and `pip check` remain unchanged. Both PR and main-push
results are retained in the local run evidence, including failed attempts.
Pytest scratch/cache directories are fresh, path-checked children of ignored
`.local/test-temp/`, avoiding dependence on Windows system-temp permissions.

For Batch 2, read PRD/implementation plan and the P01–P03 reports plus ADR 0004.
Create `codex/` branches, keep logical phase commits, open PRs to `main`, and wait
for both checks before merging. Extend the same checks with real PostgreSQL and
HTTP integration evidence as P04–P07 are completed. Do not replace this workflow
or mark later gates passed with placeholders. Stop before P08.

Repository-related schemas, operator examples, release signer identity and the
data publisher now use `DevOps_Assignment`; app/namespace/image names stay
`stellar-atlas`. The P03 sealed lock's historical URL template is explicitly
superseded by ADR 0004, preserving immutable archive/notice bytes. No data was published.

Local reproducibility:

```powershell
python tools/run.py tools-lock --verify-only --json
python tools/run.py test --json
python tools/ci_security.py --json
```
