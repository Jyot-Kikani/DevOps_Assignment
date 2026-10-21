# Batch 6 report — P19–P21

Completed 21 October 2026 under ADR 0005. **P22/P23 remain unstarted.**

| Phase | Actual outcome |
|---|---|
| P19 | Existing full-history secret/lock/publication gate passed; fake-token example rejected with exit 1. Ten public private-route checks returned 404. Web/Catalog/Journey actually run as UID 10001; database/admin/monitoring Services remain private. Exact running-release Grype evidence reused with strict threshold still failed. |
| P20 | Deleted exactly one stateless Journey pod; a different ready UID served the identical journey after 7.220 s. Git deploy change scaled Journey 1→2; normal Git revert returned it to 1. Argo reached Synced/Healthy at both revisions. Same catalog, journey and PVC survived. |
| P21 | Added guarded `demo-stop`/`demo-start` commands and a short operating/recovery guide. Actual retained-node stop/start preserved 331,312 rows, active snapshot, journey HTTP/database hash and Bound PVC. Actual failed offline search and public browser recovery captured. Batch 4 host backup/isolated-restore evidence reused. |

## Source and delivery

Batch 5's report [PR #11](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/11)
was merged as `44bfa376587809d01a59c5c699e23e85edc516ab` after checking both
required current-head jobs successful and an up-to-date base. Batch 6 uses
`codex/batch6-operations`; its PR/current-head CI are recorded below when available.
Origin/history and protected-main checks remain intact.

The live application remains the verified Batch 5 rollback release
`r39557433765-a1-2abd14c22f31`, source `2abd14c22f316c180ff163557b9690f18cfa1704`.
No application image, dependency, data, schema or scientific calculation changed.

| Deploy operation | Git revision | Observed state |
|---|---|---|
| Scale Journey to 2 | [7b64485](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/7b64485c78030f3c86eaa80041bec5e361f901fb) | Argo Synced/Healthy; Journey 2/2 |
| Normal revert to 1; left running | [82bd031](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/82bd0318aa50fa205baa5078c9aee3ffc5313d61) | Argo Synced/Healthy; Journey 1/1; app/release/scan files exactly match pre-scale `fc60b55` |

The scale-down push/convergence/persistence observation took **13.840 s**. Initial
scale-up converged, but its final output command used an invalid mixed selector;
the corrected evidence was read without another push. No scale-up duration is claimed.
P18's actual Git rollback and P05's atomic-import/role-denial evidence are reused.

## Validation and limitations

- Local quality passed **74 Python tests**, **5 frontend tests**, generated
  contracts/types, typecheck, lint and build. Focused operations/Kubernetes/delivery
  checks passed **18 tests**. The final repeated-stop adjustment passed all **7**
  lifecycle tests; hosted current-head CI remains the PR milestone gate.
- Existing Gitleaks/lock/action/publication checks passed. A generated fake token
  was safely rejected; no credential was committed or shown. Public denials covered
  metrics, admin, docs, import/migrate and internal API paths. Live UID/token-mount
  checks and ClusterIP inventories are saved. Batch 2 role-denial and Importer
  image/job evidence are unchanged and reused.
- Reused Grype 0.120.1 scan for the exact running source: Web **91 High / 17 Critical**;
  Catalog/Journey/Importer each **55 High / 0 Critical**. All strict high thresholds
  remain **failed, exit 2**. No finding suppression, new scanner, signing/SBOM or
  network-policy claim. See [the actual review](P10_IMAGE_REVIEW.md).
- Deleted pod `journey-79f85cc6cc-zm4xs` / UID
  `a4ab5421-caf5-45bc-aff0-2652a5508dac` was replaced by
  `journey-79f85cc6cc-zp8qs` / UID `5429f5a5-dde5-434c-bd63-212a1fdc6324`.
  Controller/gateway/data recovery observation: **7.220 s**. This is one node,
  not HA or a guaranteed recovery time.
- Safe-stop command took **76.404 s** including its checkpoint/tunnel checks and
  60-second Docker grace period. The node exited **137**; this is not a clean DB
  shutdown claim. Start/readiness/GitOps/persistence/tunnel/public checks took
  **225.218 s**. The exact existing node/container was retained. PostgreSQL recovered
  and the comparison passed; the unrelated `devsecops-demo` node stayed running.
- Saved restart journey `3d7f7954-edaf-4a3d-98c4-1807ee80d21d` returned the same
  HTTP body and database-row SHA-256; catalog remained **331,312** with active
  snapshot `gcns-edr3-20261013-20271720`. Bound PVC UID remained
  `c0b128bf-74cd-4b69-bf22-19b4a5a32666`. No live restore, reimport, cluster rebuild
  or destructive teardown was performed. Existing host dumps are preserved.
- Three real screenshots record local before-stop, actual failed search while
  stopped and resumed public Proxima profile. Cached geometry/profile stayed visible
  offline; a new request showed “Failed to fetch” and Retry search. Chromium uses
  software rendering; these are operational screenshots, not P22 FPS/usability results.
- Public smoke after restart passed release/API identity, real Proxima estimate,
  share/read and five private-route denials. Public browser loading/search/profile
  passed from this host. Batch 5's external-phone check is historical; no new
  external-device confirmation is claimed.
- Private monitoring recovered: both Prometheus scrape targets were up, a real
  Catalog request increased its counter, and Grafana's four-panel dashboard API
  passed. Temporary loopback forwards were closed after the check.

## Evidence, operation and handoff

Concise committed command observations: [batch6-operations.txt](evidence/batch6-operations.txt).
Selected detailed evidence stays ignored:

- `.local/reports/batch6-{security,quality}.json`, `fake-secret-rejection.json`,
  `p19-security-summary.{json,txt}`.
- `.local/reports/{pod-replace.json,p20-pod-replace.txt,p20-scale-up.json,p20-scale-down.json}`
  and corresponding scale text output; `.local/p20-deploy/` contains normal Git history.
- `.local/reports/{demo-stop.json,demo-start.json,demo-cycle.json,p21-browser-cycle.json}`;
  `p21-{demo-stop,demo-start,stopped-containers}.txt`.
- `.local/reports/batch6-monitoring.txt` — post-restart private monitoring check.
- `.local/reports/batch6-visuals/{p21-before,p21-offline,p21-resumed-public}.png` —
  visually inspected screenshots of the actual operational cycle.

Current temporary app:
<https://films-adrian-disabled-attribute.trycloudflare.com/explore>.
The original Batch 5 hostname is retired. Copy new share/view links. The app,
private monitoring, Argo and new tunnel are left running, with one app replica each.
Availability requires this host, Docker, kind, tunnel and internet; no uptime promise.

Usage: [P19 security summary](P19_SECURITY_SUMMARY.md),
[P20 operations](P20_KUBERNETES_OPERATIONS.md), [P21 runbook](P21_OPERATIONS.md)
and README. Routine commands are `demo-start`, `demo-stop`, `public-start/stop`,
`gitops-check`, `backup` and isolated `restore --target restore-check`.
No human login/MFA, paid service, global installation or persistent token was needed.
Original assets, provenance, backups, Terraform state and unrelated containers remain.
P22 final usability/performance review and P23 final acceptance/handoff are the next
boundary and were not started.
