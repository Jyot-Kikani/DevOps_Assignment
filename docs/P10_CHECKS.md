# P10 — Focused checks and basic security

Existing quality and security checks retain their names, pinned tools, frozen
dependencies, full-history exclusions/Gitleaks and real PostgreSQL/HTTP suite.
Quality now also runs the two real browser flows using the attributed five-row
fixture. CI never downloads or pretends to use the sealed full catalog. It starts
temporary loopback development APIs and Vite, restores pinned Chromium on Linux,
then stops those processes. No cluster, scanner framework or coverage gate.

```powershell
python tools/run.py test --json
python tools/run.py db-check --json
python tools/check_web_ci.py
python tools/run.py security --json
```

The CI web check needs free ports 5173/18000/18001 and the existing locked wheels
and database worker. It intentionally activates a fixture; stop the normal app
first and run `dev-up` afterwards to restore the sealed baseline. The original
full-data/backend evidence is reused because neither scientific calculations,
imported values, binary format nor backend behavior changed in this batch.
P09 separately exercised the containerized full import from an empty volume.

Frontend unit checks cover binary handling, safe URL defaults, exact 100 pc,
string IDs, local deduplication/limits and damaged storage. Browser checks cover
Explore/select/search/measurement and calculation/playback/save/share/reopen,
including frozen summaries with Catalog reads unavailable. Supplemental mobile,
save/removal and unavailable/expired/WebGL checks are in `tools/review_web.mjs`.
The HTTP 410 UI check is mocked; backend retention remains P07 real-DB evidence.

`security` first runs the existing gate, then demonstrates rejection of a clearly
fake GitHub-shaped token generated only in memory. Expected rejection is exit 1;
no actual secret is used. It then runs pinned Grype against all four exact local
image IDs with `--fail-on high`, preserving JSON findings and logs under
`.local/reports/grype-*`. Missing scanner/database or nonzero scan fails the action.
See [Grype's CLI reference](https://oss.anchore.com/docs/reference/grype/cli/).

Manifest review: no host DB/API ports; only loopback Web; separate mounted role
credentials; admin only in bootstrap; non-root application/job users; runtime
health checks, resource limits, dropped capabilities and gateway route allowlist.
Nothing deploys or publishes, and neither protected-main check is weakened.

Actual checks: 55 P10 Python tests, 5 frontend tests, drift/type/lint/build,
25 PostgreSQL/HTTP tests and both fixture-backed browser flows passed. Existing
security/exclusion checks and the fake-token rejection passed. The Grype high
threshold **failed** and remains failed: see [the review](P10_IMAGE_REVIEW.md).
ADR 0006 updates the runtime bases for real fixes but makes no clean-scan claim.
Publishing images is not authorized in Batch 3 and remains a P15 gate; these
local findings must be reviewed/remediated there before any publication decision.
