# Batch 8 — DevOps learning and demonstration guides

Documentation follow-up on **21 October 2026**. P00–P23 implementation remains
complete; this is not a new infrastructure phase. Scope: the user's requested
interactive HTML visualiser, architecture/file guide and DevOps demo guide.

## Deliverables

- [architecture_visualiser.html](architecture_visualiser.html): standalone offline
  page with delivery, platform, operations and security maps; selectable components,
  source-file links, command references, keyboard tabs and guided walkthroughs.
  It is a teaching map, not a live status dashboard or infrastructure control.
- [architecture_guide.md](architecture_guide.md): file purposes, resource ownership,
  source vs deploy branch, command entry points, change paths and concept explanations.
- [demo_guide.md](demo_guide.md): DevOps-first 12–15-minute script, preflight,
  expected results, talking points, optional operations, questions and troubleshooting.
- README and docs index link the materials. All new deliverables stay beneath
  `docs/`, within the existing automatic documentation-release exclusion.

## Baseline and scope

Clean starting HEAD and refreshed canonical remote main both matched
`71484666d4e837108f1dddf6da425fc0da32f284`. Branch:
`codex/devops-learning-guides`. Origin/history are preserved. The current
README, contribution rules, ADR 0005, Batch 7, workflows, manifests and relevant
operator helpers/phase guides were inspected for implemented behavior.

The guides distinguish CI secret checks from failed Grype thresholds, Terraform
platform ownership from Argo application ownership, source SHA from image digest
and deploy revision, and PVC persistence from host backup. They do not assert
Calico/signing/SBOM, HA, centralized logging, automatic recovery or a fresh live
deployment. Prior runtime observations remain attributed to their dated reports.

## Validation and delivery

- Locked artifact integrity: **57 artifacts passed**, no installation.
- CLI action/help inspection completed; operational demonstration commands were
  checked against the implemented dispatcher and existing phase guides.
  **16 documented CLI invocations parsed** without executing their operations.
  PowerShell wrapper argument checks verified quoted comma-separated kubectl
  resource lists and custom-column expressions stay single string arguments.
- Offline Chromium **156.0.8078.4** review passed: **32 component selections**
  across four maps, **27 guided steps**, previous/next bounds, keyboard tab
  navigation and **276 local-link checks** (including repeated references).
- All four maps fit **1440, 768, 390 and 320 px** widths without horizontal
  overflow; connector paths remained valid. No page errors or HTTP requests.
  Desktop dark/light and mobile light screenshots were inspected.
- Clipboard access was unavailable in the automated local-file browser; the
  visible manual-copy fallback was verified. No clipboard-success claim is made.
- Focused review output: ignored `.local/reports/devops-guides/review.json` and
  `desktop-dark.png`, `desktop-light.png`, `mobile-light.png` in that directory.
- Local full-history Gitleaks, publication exclusions and pinned-action checks
  passed after the implementation commit; no leaks or boundary violations.
- Implementation commit: [`3af6e5b`](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/3af6e5bdd0c5fea45a343c13fba50436e0137514).
  Delivery: [PR #15](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/15).
  Both required GitHub jobs were launched; their
  [current-head results](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/15/checks)
  are authoritative. The PR remains available for review; no merge is performed
  as part of this documentation request.

No application source, dependency lock, scientific data, original validation,
mockup, deployment manifest or workflow was changed. No cluster start/stop,
public tunnel, rollout, backup, restore or data import was executed for authoring
these materials. Runtime state and public availability were not reverified.

Human use: open the HTML in a browser and follow the demo preflight on the configured
host. Live mutation exercises are labelled; scaling/rollback refer to the existing
exact procedures. No further implementation is started.
