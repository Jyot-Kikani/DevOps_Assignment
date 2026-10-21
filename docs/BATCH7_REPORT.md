# Batch 7 report — P22–P23

Review date: **21 October 2026**. Scope is final usability/performance review
and course submission under ADR 0005. No future infrastructure is started.

| Phase | Actual result |
|---|---|
| P22 | Real desktop/mobile core flows, keyboard selection, 1151/300526 counts, observer/view links, Saved, fallback/storage denial and representative error/retry passed. Four screenshots inspected and retained. Corrected stale About availability/metadata wording. |
| P23 | Final architecture, course-topic evidence, operating/recovery links, assessment script and FR/NF/DV register assembled. Bounded clean-clone source/lock/CLI check and final public review recorded below. |

## Source and validation

Starting checkout was clean `codex/batch6-operations`, head `25eb0a2`, with
origin preserved as `Jyot-Kikani/DevOps_Assignment`. Refreshed main was `44bfa37`.
Batch 6 [PR #12](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/12) had
both current-head required checks successful and a clean/up-to-date base; it was
merged as [81a0edb](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/81a0edbe354c4e053470ed5868ab1127e880985d).
Batch 7 uses `codex/batch7-final-handoff` from that refreshed main. Protection
readback still requires up-to-date PRs, `ci / quality` and `ci / security`,
including admins, with zero mandatory human approvals.

- Local quality: **74 Python tests**, **5 frontend tests**, generated schemas/
  types, typecheck, lint and build passed. Full-history Gitleaks/publication
  exclusions passed. Existing required CI remains the PR merge gate.
- Existing **two real-API browser tests** passed against the full-data kind app.
  Supplemental desktop/mobile/fallback/expiry review and focused P22 checks
  passed; no page errors. Only the explicit aborted-request/WebGL/storage/410
  cases are injected UI conditions; the catalog, estimates and shares are real.
- [P22 review](P22_FINAL_REVIEW.md) records warm local default-map completion
  **457 ms**, profile/search/map **19/14/23 ms**. Chromium **156.0.8078.4**,
  software rendering; mobile **390×844** is emulation. No FPS/load SLO claim.
- Sealed scientific/backend/transfer/retention evidence is reused from Batches
  2/3; pod/scale/restart/restore/monitoring evidence is reused from Batches 4–6.
  No scientific input, schema, dependency lock, original mockup or validator changed.
- Canonical clean clone at `81a0edb`: clean Git status, **57 lock artifacts**
  verified and CLI `--help` passed. No dependencies, second cluster or dataset
  were installed. Both retained host dump SHA-256s matched their manifest.
- Same-host public HTTPS Chromium review passed the default map, keyboard
  skip-link focus and About source/data fields. One warm public map reload
  took **2,528 ms**; warm profile request **469 ms**. These are individual
  observations, not latency guarantees or fresh external-device evidence.

## Final runtime and delivery

At the initial final-review checkpoint, Argo was **Synced/Healthy** at deploy
`82bd0318aa50fa205baa5078c9aee3ffc5313d61`, with running source
`2abd14c22f316c180ff163557b9690f18cfa1704`, release
`r39557433765-a1-2abd14c22f31`. Source/report commits and running image commits
are distinct. Final publication and public checks after the wording fix are
recorded in the delivery addendum when actually observed.

Temporary public app:
<https://films-adrian-disabled-attribute.trycloudflare.com/explore>.
Initial public smoke passed exact release/API/data identity, real Proxima
estimate/share/read and five private-route 404s. This hostname works only while
this host, Docker, kind, cloudflared and internet are available; restart changes it.
No new external-device check is claimed; Batch 5's user-confirmed phone/mobile-data
test is reused as historical evidence.

## Evidence and handoff

Submission entry point: [P23_SUBMISSION.md](P23_SUBMISSION.md), including
architecture, course-topic matrix, runbook links and eight-minute demo script.
The [acceptance register](ACCEPTANCE.md) maps every FR/NF/DV criterion to actual
fresh or reused evidence. Screenshots:
[desktop](evidence/batch7-desktop.png), [mobile journey](evidence/batch7-mobile-journey.png),
[fallback](evidence/batch7-fallback.png), [error](evidence/batch7-error.png).
Concise command summary: [batch7-final.txt](evidence/batch7-final.txt).

Detailed ignored outputs: `.local/reports/batch7-{quality,security}.json`,
`batch7-e2e.txt`, `web-review/review.json`, `p22/review.json`,
`p23-clone-{locks.json,help.txt}` and final public/delivery observations.
The bounded clean clone is `.local/p23-clean-clone/`; it does not inherit local
credentials, data or infrastructure. It is not a second deployed environment.

Preserved host backup: `.local/backups/20261020T204752775608Z/`; manifest and two
dump hashes are checked against retained files in this batch. Batch 4's isolated
restore is reused. This older backup predates later shares; preserve the working
PVC and take a fresh `backup` before any explicitly authorized destructive work.
No teardown, reimport, restore into the working DB, login/MFA, paid service or
global installation was needed. Unrelated `devsecops-demo` stays untouched.

## Remaining limitations

Grype's actual running-release strict high threshold remains **failed, exit 2**;
the initial reused source has Web **91 High / 17 Critical**, Python images each
**55 High / 0 Critical**. No finding suppression or signing/SBOM claim. A newly
published source requires its own actual scan record, not these inherited counts.

Single-host availability, temporary hostname, software/mobile-emulated review,
historical external-phone/billing evidence, old backup age, no formal accessibility
certification and no clean-clone runtime provisioning are explicit limits.
The dated cost/configuration review confirms the existing free/local architecture
and no paid resources added; P00's user-supplied Free/$0 budgets are reused, with
no fresh account billing read. Optional HA, signing/SBOM, custom networking,
automatic recovery and strict FPS/load gates are out of scope under ADR 0005.
