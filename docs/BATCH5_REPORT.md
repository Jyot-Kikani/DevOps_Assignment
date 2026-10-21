# Batch 5 report — P15–P18

Completed 21 October 2026. **P19 has not started.** This is the course-sized
implementation under ADR 0005; final P22/P23 product acceptance is separate.

## Outcomes

| Phase | Actual result |
|---|---|
| P15 | Immutable sealed data release and four scanned GHCR images published; anonymous archive/raw/notice checks and image-manifest hashes verified. Protected required CI retained and demonstrated rejecting a failing PR. |
| P16 | Real Kubernetes app served through accountless HTTPS Quick Tunnel. User confirmed Explore, Proxima calculation/share and `/metrics` 404 from a phone over mobile data. Public browser/HTTP checks also passed. |
| P17 | Pinned namespace-scoped Argo installed; application reached Synced/Healthy at exact deploy revision, with matching live source, images and dataset. Ordered bootstrap/migration/import Jobs completed first. |
| P18 | Protected PR delivered a visible “TEMPORARY PUBLIC DEMO” label through CI → GHCR → deploy → Argo. A normal Git revert restored the prior label/source/release/digests; public checks passed again. |

Current temporary app: <https://firewire-cooking-exchanges-relatively.trycloudflare.com/explore>.
It works only while this host, Docker, kind, cloudflared and internet are available.
There is no uptime guarantee; a new tunnel gets a different hostname. Copy new
share/view links after restarting it. `public-stop` stops only the recorded tunnel.

## Source, delivery and review

- Foundation [PR #9](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/9),
  merged as [2abd14c](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/2abd14c22f316c180ff163557b9690f18cfa1704).
- The [intentional failing run](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39556102812)
  failed `ci / quality` and left the PR **BLOCKED**; security passed. That revision
  also exposed a publication mock needing the new canonical-repository boundary.
  Both failures were corrected; the temporary failing test never reached main.
  [Corrected PR CI](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39556446429)
  and [main CI](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39557121571)
  passed both required jobs before
  [initial publication](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39557433765).
- Update/fixes [PR #10](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/10),
  merged as [ee68173](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/ee68173f6f30c1fc48787ce4a8793bce0035daa3).
  Both [final-head PR CI](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39560969472)
  and [main CI](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39561460581)
  passed, followed by [update publication](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39561890748).

| State | Source / release | Deploy revision and exact image record |
|---|---|---|
| Baseline | `2abd14c`; `r39557433765-a1-2abd14c22f31` | [32882c1 / release.json](https://github.com/Jyot-Kikani/DevOps_Assignment/blob/32882c1aa2eef651479f7fd01da650a280756375/release.json) |
| Visible update | `ee68173`; `r39561890748-a1-ee68173f6f30` | [c6604d0 / release.json](https://github.com/Jyot-Kikani/DevOps_Assignment/blob/c6604d0b72b3615542bd8b1da30c12556a82172b/release.json) |
| Verified rollback; left running | Baseline source/release/digests restored | [fc60b55 Git revert](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/fc60b55fd9b8eeb0929a6e6e109879b673fc6ccf) |

The source checkout is newer than the running app **because rollback was
demonstrated**. Main/history/protection were preserved; deploy was never force
pushed. Documentation-only main releases preserve that deploy state. A deliberate
manual main publication or later application change can promote newer code again.

The [data release](https://github.com/Jyot-Kikani/DevOps_Assignment/releases/tag/data-gcns-edr3-20261013)
contains the exact frozen archive, lock, validation report and notices. Anonymous
download verified archive SHA-256
`284a83d490d701d7aaff1fb3825d0fc093a56a8ffe1869c5987ccf1f55ce46cf`,
the original raw checksum and notices. The historical sealed lock was not edited;
the resolved canonical URL is stored separately under `.local/data/`.

## Validation and limits

- Local initial quality passed **66 Python tests**, **5 frontend tests**, generated
  contracts/types, typecheck, lint and build. After the focused recovery-metadata
  regression, hosted final implementation CI passed **67 Python**, **25 real
  PostgreSQL/API**, **5 frontend** tests and **2 real-API browser flows**, plus
  four non-root image builds and the existing full-history security/lock gates.
  Focused delivery/Kubernetes checks passed **11 tests**. No redundant full-data
  backend matrix or extra scanner was introduced.
- Argo baseline, update and revert each reached **Synced/Healthy** at the exact
  Git revision. API metadata, web version/release and deployment digest references
  agreed. The retention CronJob also uses the published Importer digest.
  Proxima remained **4.24637698440337 ly / 42.4637698440337 Julian years at 0.1c**.
  Public estimate/share/read and five private-route denials passed after each
  deployment. The user external-phone confirmation is retained separately from
  local HTTP/browser observations.
- The pre-Argo journey `026833ad-b779-4fe7-884a-d43e2f33e7e8` returned identical
  persisted data after adoption, update and rollback. Catalog count remains
  **331,312**. No database restore or schema downgrade was used for rollback.
  The rollback refresh/version/calculation/share check took **15.784 s**; this is
  a command observation, not an RTO guarantee.
- Foundation Terraform applied the Argo namespace/Role/RoleBinding, then returned
  **no changes**, including after Argo bootstrap. Platform/PVC/database/monitoring
  remain Terraform-owned. Argo manages only application Services, Deployments,
  ConfigMaps and CronJob in `stellar-atlas`; no cluster-admin grant or destination
  Secret management was added. UI remains ClusterIP; metrics/admin/database stay
  private. Repeated tunnel start reused the same verified process and URL.
- The first Argo cold pull took about **10 min 39 s** and exceeded the initial
  wait. The failed report is preserved; the cached-image retry passed. Startup
  now allows fifteen minutes. An initial discovery error for an ungranted
  DaemonSet kind was resolved with resource inclusions matching the existing Role,
  without expanding its permissions. The corrected live comparison/sync passed.
- Host backup metadata now reads the actual running release instead of a stale
  Compose build record; its focused regression passes. Batch 4's unchanged manual
  backup/isolated-restore evidence is reused; no new restore claim is made here.

Both publication runs scanned all four built images with pinned Grype 0.120.1.
The original strict `--fail-on high` threshold remains **failed (exit 2)**:

| Image | Baseline High / Critical | Update High / Critical |
|---|---:|---:|
| Web | 91 / 17 | 91 / 17 |
| Catalog | 55 / 0 | 55 / 0 |
| Journey | 55 / 0 | 55 / 1 |
| Importer | 55 / 0 | 55 / 1 |

These are actual scan-time counts, not a clean-image claim or an assertion that
every match is exploitable. The update's additional certifi match and direct
Journey CA-bundle inspection are explained in [the image review](P10_IMAGE_REVIEW.md).
Findings were retained under ADR 0005, with no ignore list or threshold reduction.
The older failed Batch 3 result remains historical evidence. Signing/SBOMs are not
implemented or claimed. P10's safe local secret rejection is reused.

## Evidence, current state and handoff

Selected ignored evidence:

- `.local/reports/p15-{intentional-ci-failure.log,blocked-pr.json,release-first/}`;
  `.local/reports/batch5-{quality.json,security.json,hosted-main.log}`.
- `.local/reports/p16-{external-human.json,tunnel-reuse.json}`;
  `.local/public/{state.json,cloudflared.log}` — current URL/process record.
- `.local/reports/p17-{bootstrap-cold-pull-failed.json,bootstrap-retry.json,baseline.json,public.json,persistence.json}`.
- `.local/reports/p18-{hosted-main-full.log,release/,update.json,public-update.json,rollback.json,public-rollback.json,persistence.json,certifi-review.json}`.
- `.local/reports/batch5-visuals/p18-{before,update,rollback}.jpg` — actual public
  browser label/source/release screenshots; `public-shared-journey.jpg` records
  the real browser share. Browser rendering/phone observations are not FPS claims.
- Each release's concise `scan-summary.json` remains in its deploy history;
  full scans are also retained locally. Actions artifacts expire after three days.

Usage: [P15 publication](P15_PUBLICATION.md), [P16 public access](P16_PUBLIC_DEMO.md),
[P17 GitOps](P17_GITOPS.md), [P18 update/rollback](P18_UPDATE_ROLLBACK.md) and README.
The final documentation PR is left open for review. Its current checks are
authoritative for later report commits; implementation-run links above are not
substitutes for current-head CI. Implementation PRs #9/#10 were merged with both
required checks passing to demonstrate actual main-triggered publication.

The app, project kind cluster, private monitoring and original public tunnel are
left running with the verified rollback. The unrelated `devsecops-demo` cluster,
existing backups, original validation/mockups and sealed provenance are preserved.
No global PATH/installation, new account, persistent token or paid service was
required. Existing Git Credential Manager authentication was reused only in child
processes; human login/MFA was not automated. The user supplied the phone check;
there is no outstanding human setup action.

P19 security-summary work, P20 scaling/offline demonstrations, P21 safe-restart
work and P22/P23 final review/handoff remain unstarted.
