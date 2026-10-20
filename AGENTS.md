# Stellar Atlas agent guidance

## Scope and handoff

- This is a university DevOps assignment. Build the smallest reliable demonstration
  of the requested topics while preserving product behavior and scientific accuracy.
- The user's requested phase range is the boundary. Complete it and stop before
  the next phase; do not start future infrastructure or publication work.
- At session start, read README.md, CONTRIBUTING.md and docs/README.md. Follow
  docs/adr/0005-course-assignment-scope.md over older hardening requirements.
  Read the latest relevant BATCH*_REPORT.md for actual status, then the relevant
  sections of docs/IMPLEMENTATION_PLAN.md, PRD.md, ACCEPTANCE.md and phase guides.
  Read contracts, code, tests and other ADRs only as relevant to the change.
- Batch reports hold changing status and evidence; this file holds standing rules.
  Distinguish planned, implemented, tested, locally running and publicly available.

## Repository and environment

- Use only https://github.com/Jyot-Kikani/DevOps_Assignment. Preserve origin and
  history. Read ADR 0004 before interpreting historical repository/publication URLs.
- Recheck Git state and current remote main before edits. Use codex/ branches,
  meaningful commits and PRs. Merge only with an up-to-date branch and passing
  required ci / quality and ci / security checks. Never bypass protections.
- Use free tools, existing hardware and pinned project-local tools/dependency locks.
  No AWS, paid hosting, purchased domains or expiring credits. The deployment target
  is local kind Kubernetes with Cloudflare Quick Tunnel in its planned later phase.
- Inspect existing tools/resources before setup changes. Sandbox access denial is
  not proof of a broken installation. Preserve unrelated containers and clusters.
  Human login/MFA remains with the user; keep credentials and generated secrets out
  of Git, logs and screenshots.
- Preserve validation/, design/mockups/, the sealed P03 catalog and provenance.
  Inspect validation scripts before running; some download and overwrite outputs.
  Mockups guide appearance, never scientific star coordinates.

## Checks, evidence and efficiency

- Run focused checks for changed behavior and the required CI at PR milestones.
  Cover normal paths and representative failures; reuse unchanged backend/full-data
  evidence. Repeat expensive checks only for relevant changes or required acceptance.
- Grype scan/review/documentation is sufficient for this course scope. Do not make
  zero High/Critical findings a prerequisite for future batches. Preserve actual
  findings and failed threshold results; do not silently waive or weaken checks.
- Avoid extra scanners, exhaustive error matrices, coverage quotas, custom networking,
  strict performance gates and other optional infrastructure without a concrete need
  or explicit request. Never invent signer/SBOM values or implemented capabilities.
- Capture only important evidence. Saved command output is acceptable for terminal
  demonstrations; use a few useful browser screenshots where available. Keep detailed
  logs, raw data, state and backups ignored; commit only concise sanitized evidence.
- Keep prompts, progress updates and reports concise. Read guidance once per session,
  search relevant sections, limit tool output and avoid repeated full-document reads.
  Do not generate elaborate evidence systems or rerun passing checks without cause.
- Finish each batch with docs/BATCH<N>_REPORT.md: phase outcomes, changes, actual
  validation, selected evidence paths, commit/PR links, human actions and limitations.
  Update relevant usage documentation and leave the next phase unstarted.
