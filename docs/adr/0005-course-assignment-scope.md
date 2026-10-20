# ADR 0005 — Keep future work appropriate for a course assignment

- Status: accepted by the user, 20 October 2026.
- Supersedes: production-hardening requirements in the original PRD and implementation plan.
- Preserves: ADRs 0001–0004, completed P00–P07 work, sealed catalog/provenance and existing CI checks.

## Context

The user clarified that Stellar Atlas is a simple university DevOps assignment,
not a startup product, and asked to reduce excessive security/error checking and
infrastructure setup in the future plan. No faculty rubric or handout is present
in this repository; the earlier ambitious plan must not be treated as proof that
every proposed tool or failure scenario is required by the course.

## Decision

Implement the smallest reliable demonstration of each core topic: Docker,
local kind Kubernetes, a small Terraform platform, protected-main CI, image
build/scan/publication, Argo CD delivery, Git rollback, basic monitoring, one
manual backup/isolated restore and Cloudflare Quick Tunnel public access.
Keep the planned product behavior, scientific correctness and zero-cost limits.

Use default kind networking and one application replica normally. Demonstrate
scaling briefly. Keep credentials out of Git, databases/admin surfaces private,
existing role separation, input validation and non-root application images.
Retain existing Gitleaks and add one Grype image scan with one safe rejected
example; avoid building a larger security framework.

Signing/SBOMs, extra scanners, custom CNI/default-deny policy matrices, CI
clusters, exhaustive hostile-input/fault/race campaigns, fixed coverage quotas,
automatic disaster recovery and strict load/FPS SLOs are optional. Implement an
optional item only for a concrete observed need or explicit course requirement.
Pinned tools, example directories and old command inventories do not require
installing or building unused components.

Run focused checks while editing and the existing CI at milestone PRs. Test the
normal path plus a representative failure where useful; record manual demos
and screenshots where sufficient. Reuse unchanged backend/full-data evidence.
Repeat full-data/browser checks when relevant behavior changes or at final
acceptance, rather than for every unrelated change.

## Consequences

The revised PRD, implementation plan and acceptance register control future
checks. Optional work is not a failed submission gate. Existing implementation,
required CI job names, branch protections and historical reports remain intact.
In P11, explicitly simplify the draft release schema/tests to match the smaller
release record; never fabricate signer/SBOM metadata to satisfy obsolete fields.
This decision edits documentation only and does not start P08.
