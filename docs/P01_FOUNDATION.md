# P01 repository foundation — completed

The repository layout, contribution/security guidance, original-software license,
upstream-data notice, operator example and public configuration schema are present.
The existing main branch, identity and origin were preserved. Mockups and sanitized
feasibility evidence are now tracked; raw catalog/bin files remain ignored.

`tools/run.py` dispatches through the stdlib-only `stellar_ops` package. `doctor`
reports real failures; `tools-lock` verifies artifact hashes or restores exact
frozen tools without selecting newer versions. Every mutation target must stay
under `.local/`, and Kubernetes writes must explicitly check the project context.
Future actions are unavailable until their implementation phase.

Verified:

- All four local Python environments installed from committed, SHA-256-locked
  Windows requirements; `pip check` reports no broken dependencies in each.
  Linux runtime locks remain separately preserved. No global package/PATH change.
- Portable Node 24.22.0 completed clean npm installation, scaffold build, lint and
  typecheck. The atlas itself is not implemented; frontend/e2e scripts are configured
  and will fail if no tests exist, rather than claiming a passing application suite.
- A fresh temporary clone with no original environment/cache can invoke Python
  help and verify all 50 lock artifact hashes from a different current directory.
  A deliberately altered clone lock is rejected. No second-machine claim is made.
- Unsafe filesystem targets and an unrelated Kubernetes context are rejected.
  Unimplemented commands fail. PowerShell wrapper syntax parses successfully.
- Staged secret scan found no leaks; raw catalog, local credentials/state and
  dependency environments are excluded by Git/build-context rules.

Host notes: local PowerShell script execution is restricted; use the documented
Python equivalent without weakening global policy. A fresh doctor correctly
reports port 9090 occupied by `p8-food-orders-prometheus-1`. That unrelated Practical 8
container was preserved. This batch does not bind that port; it must be freed by
the operator before the later monitoring demonstration. Other prerequisite checks
passed. This is recorded explicitly, not treated as a green full-host doctor run.

Evidence is under ignored `.local/reports/p01-*.json`/logs and
`.local/reports/phases/P01.json`. Publication, database setup and deployment have
not been performed. P02 and P03 follow within the authorized batch.
