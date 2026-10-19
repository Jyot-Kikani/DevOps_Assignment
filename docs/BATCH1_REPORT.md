# Batch 1 — P01–P03

Completed locally on 2026-10-19. Stopped before P04. No push, GitHub release,
cluster, database, public tunnel or paid service was created in this batch.

## Results

| Phase | Result | Evidence |
|---|---|---|
| P01 governance/tooling | passed | `P01_FOUNDATION.md`; ignored `.local/reports/phases/P01.json` |
| P02 contracts/primitives | passed | `P02_CONTRACTS.md`; ignored `.local/reports/phases/P02.json` |
| P03 dataset sealing | passed | `P03_DATA.md`; ignored `.local/reports/phases/P03.json` |

All four Python environments were installed from hashed third-party locks and
passed `pip check`. All four first-party packages build as wheels and install
without runtime imports from sibling directories. A fresh temporary clone passed
dispatcher/lock checks from another directory; a modified lock was rejected.

Final Python unit/contract suite: **37 passed**. Frontend: **3 passed**, typecheck,
lint and production scaffold build passed. Schema and pinned TypeScript generation
checks passed. The pinned FastAPI/Starlette test client emits one nonblocking
HTTPX deprecation warning; no dependency was silently upgraded to suppress it.
These checks do not constitute database, browser E2E or application acceptance.
All 37 FR/NF/DV criteria remain not run until their full evidence exists.

Full catalog: **331,312 unique rows**, 300,526 within 100 pc, 1,151 within 50 ly,
142 within 25 ly. Coverage/percentile/unit checks passed. Two repeated seals have
identical archive and metadata bytes. Fresh loopback download/extraction verified
compressed and raw SHA-256 values. Identical staging was reused; changed assets,
bad checksums, malformed/duplicate/nonfinite rows, bad units and reversed intervals
were rejected. Mock GitHub API tests cover private-repository denial, remote
digest conflict, exact reuse and missing-only uploads; no remote release was made.
Original validation and mockup hashes are unchanged. Raw files/archives remain ignored.

## Failures and human actions

`doctor` currently returns failure because port **9090** is held by the unrelated
`p8-food-orders-prometheus-1` container. It was preserved. This does not block
P01–P03; the operator must free that port before the later monitoring phase.
Other checked prerequisites passed in the normal Windows session.

Local PowerShell script execution policy blocks direct `ops.ps1` execution.
Its syntax passes and the equivalent Python dispatcher works from another directory.
Use the documented Python commands; no global policy change is needed.

Sandbox access denials were distinguished from actual host failures. SIMBAD's
Python certificate-chain failure and sandbox Schannel access denial were resolved
using normal-session Windows TLS verification; certificate checking stayed enabled.
The two verified aliases and official notices have URLs/retrieval hashes.

**No immediate human account, login, MFA or setup action is required.** Actual
GitHub publication and external HTTPS verification remain P15/P16 gates.

## What changed

- Repository governance: root ignore/build-context/line-ending rules, MIT software
  license, security/contribution guides, CODEOWNERS/PR template, configuration
  examples and directory scaffolding; existing validation/design assets retained.
- Reproducible tooling: stdlib host dispatcher, path/context guards, frozen-tool
  restoration/integrity checks, Windows Python hash locks alongside Linux locks,
  isolated environments, frontend package/scripts/locks, provider-only Terraform
  declarations/locks and attributed vendored manifests. No infrastructure resources.
- Contract foundation: service/job wheel projects; stdlib common IDs, units,
  calculations, errors, logging and binary codec; typed API scaffolds; OpenAPI,
  public/release/phase/map schemas; pinned isolated type generator and generated
  TypeScript; independent unit/contract/frontend tests and attributed tiny fixtures.
- Data preparation: streaming validator, `data-seal`, immutable `data-publish`
  staging/explicit GitHub path, fresh-cache checker, committed small snapshot lock,
  validation report, two checked aliases, official notice archives and provenance.
- Documentation: ADRs, P01–P03 evidence summaries, current acceptance register,
  bootstrap/reading instructions and this report. Detailed local diagnostics and
  phase reports are ignored; software changes have one local commit per phase.

Only project-local environments, tools, caches, build outputs, archive copies,
fixtures, checks and reports were created under `.local/`. No global PATH,
execution policy, Git identity/origin or existing unrelated containers were changed.

The exact source diff for this batch starts after P00 commit `a5864ca` and ends
at the P03 commit. Use `git diff --name-status a5864ca HEAD` for the complete file
inventory. P01 commit is `b0671f8`; P02 is `b0ce296`. The final P03 SHA is recorded
in `.local/reports/phases/P03.json` and the completion message.
