# Contributing

Read README.md, docs/PRD.md and docs/IMPLEMENTATION_PLAN.md before changing scope.
Use a `codex/` branch for implementation work. Keep changes in logical phase
commits and use pull requests to `main` now that early CI is introduced. Wait for
`ci / quality` and `ci / security` to pass before merging. Include the problem,
resulting behavior and actual validation. This is the development procedure;
technical merge enforcement is a separate repository-rule gate, not assumed on
the currently private Free repository.

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
private visibility and zero-paid-usage budgets unless the user explicitly changes
that decision. Full security/integration checks are added in their plan phases;
an early CI pass does not establish a deployed or complete application.
