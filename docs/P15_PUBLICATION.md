# P15: trusted-main publication

The existing `ci / quality` and `ci / security` names/protections remain required.
Quality also builds four non-root images with a **build-only** importer context;
those CI images contain no real catalog and are never published.

Publish sealed data once, from the existing clone:

```powershell
python tools/run.py data-publish --github --repository Jyot-Kikani/DevOps_Assignment --json
python tools/release.py data-check
```

Existing release bytes are compared, never overwritten. The original sealed lock
is preserved; the resolved destination is written under ignored `.local/data/`.
`data-check` downloads anonymously and verifies compressed/raw bytes and notices.

After successful **main** CI, `release.yml` checks latest main and both required
checks, downloads the verified public data, builds/scans four images, publishes
GHCR digest references and pushes generated application manifests to `deploy`.
Fork PRs never receive publication permissions. One concurrency group serializes
releases; stale main cannot promote. No cluster credentials enter Actions.
Documentation-only main commits keep the existing deployment, including a Git
rollback; manual main dispatch can explicitly republish if wanted.

First GHCR publication may create private packages. In each package's GitHub
settings, select **public** once; no new account/token is required. Anonymous
manifest verification must pass before deploy promotion. Rerun the main release
workflow after changing visibility if the first run stopped there.

Grype runs once per built image with the original `--fail-on high` threshold.
Scanner errors abort; threshold failures remain **failed**, with counts and raw
reports retained for three days and a concise summary committed on `deploy`.
ADR 0005 permits publication with reviewed findings; this is not a clean scan.
See [the existing review](P10_IMAGE_REVIEW.md). No signing/SBOM claim is made.

`deploy` holds only `app/app.json`, `release.json` and `scan-summary.json`.
Publication is distinct from a verified running deployment. See Batch 5 for
actual PR, run, anonymous-access and deployment evidence.
