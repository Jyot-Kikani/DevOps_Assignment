# Contributing

Read README.md, docs/PRD.md and docs/IMPLEMENTATION_PLAN.md before changing scope.
Use a `codex/` branch for implementation work. Keep changes in logical phase
commits; after repository protection is enabled, use pull requests and the
required checks. Include the problem, resulting behavior and actual validation.

Use the frozen Node/Python toolchain and committed dependency locks. Do not add
paid services or change the architecture without recording the accepted decision.
Keep original validation and design references; never rerun their downloader
scripts as validators. New source data is a separately versioned candidate.

Run the appropriate documented checks. A missing required check is a failure,
not a skip. Never claim a build, mockup or dependency installation proves a live
deployment. Review staged paths and scan for secrets before committing. Raw
catalogs, credentials, state, backups and private evidence must remain ignored.
