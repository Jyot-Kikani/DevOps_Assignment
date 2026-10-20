# P11 — Local release-image preparation

The explicitly revised `contracts/release.schema.json` now describes actual
source/repository/release IDs, UTC creation time, the real sealed dataset and
checksum, four immutable image references/manifest digests and compatibility
versions. It no longer requires signer identity, SBOM hashes or invented
verification results. No signing or SBOM is claimed. Scientific/API contracts
are unchanged. Local image tags must match their role and source SHA; mutable
registry tags, fixture datasets, dirty release source and mismatched identities
are rejected.

```powershell
# Commit implementation first: images-build rejects any uncommitted source.
python tools/run.py images-build --json
python tools/run.py dev-up --no-build --json
python tools/run.py images-check --json
python tools/run.py security --json
```

`images-build` builds each image once from the same clean commit. It verifies the
sealed gzip/raw/notice hashes before staging the isolated importer asset. It
records Docker's real immutable local image IDs and OCI manifest digests in
ignored `.local/release.json`, with the real source SHA baked into every image
and Web's `/version.json`. Dirty dev builds are explicitly marked and cannot
validate as release candidates. `dev-up --no-build` then runs exactly those
prepared images. The mounted `/release.json` reports their actual local identity.

`images-check` validates non-root users, image/source/digest identity, running
container identity/health, installed Python dependency consistency, required
API/migration/import/maintenance modules, gateway version/data metadata and a
real journey calculation. Explicit startup jobs exercise packaged migrations
and the full sealed import/reuse. The scan always preserves its actual exit code
and findings; see [P10 review](P10_IMAGE_REVIEW.md).

An immutable local Docker image ID is usable on this machine; it is not a public
GHCR artifact. No remote registry digest, download URL, signature or SBOM value is
invented. These are local preparations for P15. Publication and public app
access remain later phases. Known base-image scan findings must not be described
as a passing high-threshold scan or silently carried into a publication decision.
Kubernetes starts in P12 and is not created here.

Actual preparation: clean commit `d6d7752157edad63394b64b83ce0510576105f49` after the stable local-link fix
built once; schema, packages/modules, all image/source/digest/user identities,
running health, local API/browser smoke and restart persistence passed. The
Grype threshold failed with the counts recorded in BATCH3_REPORT.md. Local image
preparation is complete; clean-scan publication readiness remains unresolved.
