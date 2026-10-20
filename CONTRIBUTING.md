# Contributing

Read README.md, docs/PRD.md and docs/IMPLEMENTATION_PLAN.md before changing scope.
Use a `codex/` branch for implementation work. Keep changes in logical phase
commits and use pull requests to `main` now that early CI is introduced. Wait for
`ci / quality` and `ci / security` to pass before merging. Include the problem,
resulting behavior and actual validation. GitHub enforces PRs and both checks on
the public repository's `main`, including administrators. Branches must be up to
date; force pushes and deletion are disabled. No second-person approval is required.

Use the frozen Node/Python toolchain and committed dependency locks. Do not add
paid services or change the architecture without recording the accepted decision.
Keep original validation and design references; never rerun their downloader
scripts as validators. New source data is a separately versioned candidate.

Run the appropriate documented checks. A missing required check is a failure,
not a skip. Never claim a build, mockup or dependency installation proves a live
deployment. Review staged paths and scan for secrets before committing. Raw
catalogs, credentials, state, backups and private evidence must remain ignored.

The only remote repository is `Jyot-Kikani/DevOps_Assignment`; preserve `origin`
and its history. Never create a replacement `stellar-atlas` repository. Keep
public visibility chosen by the user and zero-paid-usage budgets. Full
security/integration checks are added in their plan phases;
an early CI pass does not establish a deployed or complete application.

For future work, follow [ADR 0005](docs/adr/0005-course-assignment-scope.md). Run focused checks for the actual change and retain both existing required CI jobs. Reuse unchanged evidence; do not add scanners, exhaustive failure matrices, coverage targets or infrastructure solely for defensive completeness. Manual course demonstrations are valid evidence.
