# Batch 7 report — P22–P23

Completed **21 October 2026**. Scope is final usability/performance review
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

Implementation [7cdcb85](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/7cdcb85f2b9733c4c4ca1be035b538259f1a75db)
was merged through [PR #13](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/13)
as **`d44d639309d668ef8f74f41b20b319a9b601d76c`**, after both
[current-head checks](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39572258725)
passed on an up-to-date base. Both [main checks](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39572800136)
and [trusted publication](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39573285891)
then succeeded. Final running release is **`r39573285891-a1-d44d639309d6`**.

Final Argo: **Synced/Healthy**, deploy
[`6c5f8e67b3bb92a60ade0b5e4da828bd9a240663`](https://github.com/Jyot-Kikani/DevOps_Assignment/tree/6c5f8e67b3bb92a60ade0b5e4da828bd9a240663).
Web/Catalog/Journey are each **1/1**, with digests matching the
[published release record](https://github.com/Jyot-Kikani/DevOps_Assignment/blob/6c5f8e67b3bb92a60ade0b5e4da828bd9a240663/release.json).
The workflow also verified anonymous access to all four image digests. Data remains
`gcns-edr3-20261013-20271720` with its unchanged raw checksum and schema/model versions.

Temporary public app:
<https://bottles-milk-ethnic-macintosh.trycloudflare.com/explore>.
Final public smoke passed exact release/API/data identity, real Proxima
estimate/share/read and five private-route 404s at **16:22 IST**. Same-host public
Chromium showed the corrected About wording and exact source/data/release;
the screenshot was inspected. One final warm map reload took **1,488 ms** and
profile request **225 ms**. Earlier 457-ms local/2,528-ms public observations
remain separate checkpoints, not repeated benchmarks or guarantees.

The former `films-adrian-disabled-attribute` hostname is **retired**: its DNS
failed and the live process reported provider `Tunnel not found`. Normal
`public-stop`/`public-start` replaced only the verified project tunnel. Copy new
view/share links; old records remain in the same database. This hostname works only while
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
`p23-clone-{locks.json,help.txt}`, `batch7-final-{gitops,public-smoke,release,scan-summary}.json`,
`batch7-release-artifact/`, `p23-public.json` and `p23-public-about.png`.
The bounded clean clone is `.local/p23-clean-clone/`; it does not inherit local
credentials, data or infrastructure. It is not a second deployed environment.

Preserved host backup: `.local/backups/20261020T204752775608Z/`; manifest and two
dump hashes are checked against retained files in this batch. Batch 4's isolated
restore is reused. This older backup predates later shares; preserve the working
PVC and take a fresh `backup` before any explicitly authorized destructive work.
No teardown, reimport, restore into the working DB, login/MFA, paid service or
global installation was needed. Unrelated `devsecops-demo` stays untouched.

## Remaining limitations

The final source's fresh Grype 0.120.1 scan is **failed, exit 2 for every image**:

| Image | High | Critical |
|---|---:|---:|
| Web | 91 | 17 |
| Catalog | 55 | 0 |
| Journey | 55 | 1 |
| Importer | 55 | 1 |

Exact [scan summary](https://github.com/Jyot-Kikani/DevOps_Assignment/blob/6c5f8e67b3bb92a60ade0b5e4da828bd9a240663/scan-summary.json)
and raw downloaded artifact were reviewed. The Journey/Importer Critical match is
`GHSA-6q48-6c7w-9gw2`, certifi `2026.10.18`, with `2026.10.19` suggested by the
scanner. It is the same advisory reviewed in P18; the older Journey bundle/root
inspection is historical and was not repeated on this image. This final version
match is retained as unresolved; no dependency/trust override, suppression,
passing-threshold or signing/SBOM claim is made. See [image review](P10_IMAGE_REVIEW.md).

Single-host availability, temporary hostname, software/mobile-emulated review,
historical external-phone/billing evidence, old backup age, no formal accessibility
certification and no clean-clone runtime provisioning are explicit limits.
The dated cost/configuration review confirms the existing free/local architecture
and no paid resources added; P00's user-supplied Free/$0 budgets are reused, with
no fresh account billing read. Optional HA, signing/SBOM, custom networking,
automatic recovery and strict FPS/load gates are out of scope under ADR 0005.
