# Batch 4 — P12–P14

Implemented and locally verified on **21 October 2026 (Asia/Kolkata)**.
Started from clean, freshly fetched main `16d99d15175b443b1f5bc4583e597f9f60964dc1`.
Only remote: `Jyot-Kikani/DevOps_Assignment`. **Stopped before P15.**

## Phase outcomes

| Phase | Result |
|---|---|
| P12 | One-node `stellar-atlas-demo`, pinned kind 0.33.0/Kubernetes 1.35.8, default CNI/local-path storage, loopback API/gateway, private project kubeconfig. Terraform foundation/runtime roots own namespaces, protected 10 GiB PVC and PostgreSQL. First applies, no-change plans and label drift/repair passed. |
| P13 | Exact clean-source P11 image digests loaded and checked in kind CRI. Ordered bootstrap/migration/sealed-import Jobs, one replica per app, probes/limits/non-root containers, private DB DNS and daily UTC retention CronJob. Real gateway application and restart/share checks passed. |
| P14 | Terraform-owned private Prometheus/Grafana, provisioned four-panel dashboard, manual host backups of both databases and verified isolated restore. Original working database/PVC and host backups retained. |

Implementation and PR links are recorded in the final validation addendum below.
The existing `ci / quality` and `ci / security` names and protections are unchanged.

## Actual validation

- Platform: node/CoreDNS/PostgreSQL ready, `standard` local-path provisioner;
  both roots validated/applied and returned no changes. A namespace `demo` label
  was deliberately changed, detected by Terraform, repaired and replanned clean.
  Final plans after monitoring are recorded separately below.
- Gateway: **331,312** total rows, **300,526** within 100 pc, **1,151** within 50 ly,
  **142** within 25 ly. Real Proxima search and Sun→Proxima calculation:
  **4.24637698440337 ly**. Immutable share round-trip and identical HTTP payload
  after Journey workload replacement passed; measured replacement/recovery **5.103 s**.
  Nine private/admin/metrics/internal routes returned 404; public request IDs replaced.
- Ordered Jobs completed, including the actual sealed full import from an empty
  Kubernetes database. Daily 02:00 UTC retention CronJob installed; one manual
  execution passed. Existing role isolation/science/controlled-clock expiry proofs
  are reused from Batch 2; application code and sealed data were not changed.
- Local quality: **60 Python tests**, **5 frontend tests**, contract/type drift,
  typecheck, lint and production build passed. A subsequent focused regression
  suite passed **5 tests**, including the new gateway propagation case. Final
  hosted results are recorded below; no redundant full-data/backend matrix was added.
- Recovery: custom-format archives for Catalog (**38,100,340 bytes**) and Journey
  (**9,892 bytes**) stored in a current-user-only host directory. SHA-256 hashes
  verified before restore. Unique target `stellar-restore-96cc613b` recovered
  **331,312** rows, exact active snapshot and an identical saved-journey row hash.
  Original gateway/journey remained valid. Only that temporary namespace was removed.
  Backup took **27.455 s**; restore/check/cleanup took **84.850 s**. These are
  observations, not RPO/RTO guarantees.
- Committed lock verification passed (57 artifacts). Protected validation/mockup/
  data paths remain unchanged from the starting main. No original downloader was run.

Monitoring, final state checks, visual evidence and final-head CI are recorded
in the final validation addendum below.

## Runtime and selected local evidence

Application: `http://127.0.0.1:8080/explore`. Separate project kubeconfig:
`.local/kubernetes/config`, context `kind-stellar-atlas-demo`. The existing unrelated
`devsecops-demo` cluster remains untouched. Batch 3 Compose containers were stopped
to free 8080; their volume remains intact. Kubernetes app/database/monitoring remain
running. Monitoring uses temporary loopback port-forwards, not host/public Services.

Application source remains the clean P11 source
`d6d7752157edad63394b64b83ce0510576105f49`, release `local-d6d7752157ed`.
All four original OCI digests were verified after loading into kind. The image
source is intentionally different from this infrastructure commit. See
[Batch 3's exact image record](BATCH3_REPORT.md#exact-prepared-release-record).

Selected ignored evidence:

- `.local/reports/p12-check.json`, `demo-bootstrap.json`, `p13-check.json`.
- `.local/terraform/{foundation,runtime}/` — actual validate/plan/apply logs,
  local state and saved plans. The final plan logs supersede earlier plan output.
- `.local/reports/batch4-quality.json`, `monitoring-up.json`, `monitoring-check.json`.
- `.local/reports/backup.json`, `restore.json`.
- `.local/reports/batch4-visuals/{kubernetes-explore,grafana-dashboard}.png` —
  visually inspected real Kubernetes UI and provisioned charts; Chromium 156.0.8078.4
  with software rendering. No GPU/performance/public-path claim is inferred.
- `.local/backups/20261020T204752775608Z/` — both archives, hashes, sample and release
  manifest; directory name uses UTC. Saved shared journey:
  `9efdcea1-ff49-4ba1-9c6f-81fac8a8656e` (30-day retention).

Usage: [P12](P12_KUBERNETES.md), [P13](P13_LOCAL_DEPLOYMENT.md),
[P14](P14_MONITORING_RECOVERY.md) and README. `ops.ps1` dispatches to the same
Python commands. No global PATH, execution-policy or installation change was made.
Existing Git Credential Manager authentication is reused only in child-process
memory. **No human login/MFA, new account, paid service or setup action was needed.**

## Resolved issues and limits

The first restart check encountered non-JSON gateway output. A bounded wait for
gateway endpoint propagation and a focused regression were added; the corrected
live restart/share check passed. A diagnostic console print hit Windows Unicode
encoding; normal JSON reports remain readable and escaped as needed. Initial
Grafana image pull took several minutes; both monitoring pods reached readiness
without restarts. Kubernetes metrics-server is not installed; the scope uses
existing application metrics rather than `kubectl top`.

The **Batch 3 Grype high-severity threshold remains failed** with the actual
findings/review preserved. No app image was changed, rebuilt, rescanned or published
in this infrastructure batch. ADR 0005 allows local demonstration with those
findings recorded; this report does not convert the scan to a pass.

Monitoring history is ephemeral (Prometheus retention 24 h). Dumps are sequential,
not an atomic cross-database snapshot; avoid writes during the demo backup.
Isolated restore checks data with ownership/grants omitted; role bootstrap and
application reconnection would be separate steps for a real rebuild. Browser-local
bookmarks are outside the PostgreSQL backup. Node/PVC persistence is not a backup;
cluster deletion can destroy local-path data. No destructive teardown is provided.

No Calico, custom policies, exporter/alerting suite, scheduled backup, signing/SBOM
framework or CI cluster was added. **P15 has not started:** no data/image release,
publication workflow, deploy-branch promotion, Argo installation or public tunnel.
Scaling/rollback/public-access and final P22/P23 acceptance remain later work.

## Final validation and review

- Implementation: [fd912de](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/fd912de6fe5c705497aed398200b2abc2453c603).
  Review: [PR #8](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/8).
- Both final Terraform plans returned **no changes**, including runtime with
  monitoring enabled. Credential-value checks found none of the six generated
  passwords in either Terraform state.
- Prometheus reported **2/2 targets up**. The deliberate gateway request changed
  the Catalog meta counter from **17 to 18**. Authenticated Grafana API confirmed
  all four provisioned panels; final screenshots show real availability/request/
  duration data and zero failures for healthy services. Monitoring pods were rolled
  after provisioning changes and the check repeated successfully.
- Local full-history Gitleaks/publication exclusions/action pins passed at the
  implementation commit. The strict image scan was not rerun for unchanged images;
  its earlier failure remains preserved above.
- Hosted [implementation CI run 39496055260](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39496055260)
  passed both required jobs at `fd912de`: **61 Python**, **25 PostgreSQL/API**,
  **5 frontend** tests and **2 real-API browser flows**, plus the existing contracts,
  build, locks and full-history security gates. Saved output:
  `.local/reports/batch4-hosted-implementation.log`.
  The [PR's current-head checks](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/8/checks)
  track later documentation/report commits. A historical pass is never substituted
  for the latest head. The PR is left open for review; no merge or protection bypass
  is part of this batch.
