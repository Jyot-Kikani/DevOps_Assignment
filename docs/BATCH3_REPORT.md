# Batch 3 — P08–P11

Implemented and locally verified on **21 October 2026**. Stopped before P12.
Started from clean, freshly fetched main `f111dd6d2f59b7af7ca0e085bef0d3e8ca58185f`.
Only remote: the public `Jyot-Kikani/DevOps_Assignment` repository.

**Outcome:** usable local application, complete persistent Compose, focused tests
and clean-source local image/metadata preparation. The strict Grype high-severity
gate remains **failed**, so clean-scan publication readiness is not achieved.
No image/data publication or public app access is claimed. This report does not
convert a scanner failure into a pass.

## Phases and exact source commits

| Phase | Resulting behavior | Source commit |
|---|---|---|
| P08 | Real Explore/Journeys/Saved/About; bounded Three.js point cloud loading and picking; layers/camera/observer view links; profiles/5-neighbor separation; server measurements/calculations; opt-in playback; immutable 30-day shares; capped/deduplicated local saves and fallback states | [43d58dc](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/43d58dce2c16e3fc0d1e980970dec3bed72c4502) |
| P09 | Four non-root images; gateway allowlist/deep links/body/read/share limits; role-specific secrets; explicit bootstrap/migrations/sealed import; persistent named volume; dev-up/dev-down/smoke/restart checks | [1a4e49f](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/1a4e49fa1d0409e0d571435a2a3c5317cd86d421) |
| P10 | Existing checks preserved; 2 real-API fixture browser flows added to quality; focused UI fixes; fake-secret rejection; real four-image Grype command and findings review; pinned Trixie runtime update in ADR 0006. Tests pass; Grype high threshold fails | [ae2ef17](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/ae2ef17) |
| P11 | Explicitly simplified release schema/tests; clean-source builds; actual source/data/image identity; package/non-root/running-image smoke. Local preparation passes; image-security limitation remains | [96a6c03](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/96a6c03e5b357d6eb4947d5c4021e6bb46ee62de) |

Review the full inventory in [PR #6](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/6/files).
The [stable saved-link fix](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/d6d7752157edad63394b64b83ce0510576105f49) reuses calculation keys so list changes do not change a reopened journey. The existing protected workflow is used: PR, up-to-date branch and both required
`ci / quality` and `ci / security`, admins included; zero mandatory human approvals.
No protection is bypassed or changed.

## Actual validation

- **56 Python unit/contract tests**, **5 frontend tests**, contract/type drift, typecheck, lint and production build passed.
- **25 existing PostgreSQL/HTTP tests** passed. No exhaustive new backend matrix or repeat full-data benchmark was added.
- Both fixture-backed CI browser flows passed locally. Hosted [run 39483378740](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39483378740) passed both required checks, including the new Linux/Chromium browser step, at source 96a6c03. The [saved-link implementation run 39485379417](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39485379417) also passed both checks. Final report-head/merge checks are tracked by the PR; this historical pass is not substituted for final-head checks.
- Both full-catalog browser flows passed through the clean-image Nginx gateway: Explore/count/search/keyboard selection/3D measurement and journey calculation/play/pause/local save/share/frozen reopen, including Catalog-offline frozen summaries. The final regression calculates/saves two distinct real speeds, reopens and resaves the first, then reloads its stable local link.
- Additional local interaction review passed: layer and observer/camera share-link round trip, return home, real point picking with labels off, and orbit changing camera state.
- All four routes were checked at **390×844** with no horizontal overflow. Desktop **1440×900** and mobile screenshots were visually inspected. Save/reload/remove/clear cancellation, API outage and usable WebGL fallback passed. The 410 UI check used an explicitly mocked response; real expiry evidence is reused from P07.
- Fresh application startup from an **isolated empty PostgreSQL volume** imported the sealed baseline and passed smoke. Only that unique temporary test project/volume was removed, and the original app restored. Repeat normal startup passed.
- A real immutable share survived restarting PostgreSQL and all three app containers with identical JSON. This also passed on the Trixie image set at 96a6c03; unchanged persistence behavior is reused for the later saved-link-only fix. Named volumes are not host backups; backup/restore remains P14.
- All four clean-source images passed package/module/non-root identity checks; runtime images matched the exact recorded IDs and were healthy. Source/release/data identity and a real Sun→Proxima calculation passed: **4.24637698440337 ly**.
- Nine private/admin/internal routes returned **404** through Nginx. PostgreSQL/APIs have no host ports; only `127.0.0.1:8080` is published. Public request IDs are replaced.
- Frozen locks/action pins/publication exclusions/full-history Gitleaks passed. A clearly fake in-memory GitHub-shaped token was rejected with the expected **exit 1**; no actual credential was used.
- **13 original validation/mockup files rehashed unchanged**. Sealed snapshot/notice/provenance bytes and historical metadata are unchanged. No downloader validation scripts were run.

Browser: pinned Chromium **156.0.8078.4**, software rendering. This establishes
functional behavior, not laptop GPU/FPS, strict performance or public-path results.
The Vite bundle warning remains advisory: approximately 216 KiB gzip including Three.js.
The existing FastAPI/Starlette HTTPX deprecation warning remains nonblocking.

## Image/security results

The real Grype 0.120.1 scan uses `--fail-on high` without exclusions or a severity
downgrade. It exits **2** for every final image. Scanner match counts:

| Final image | High | Critical | Exit |
|---|---:|---:|---:|
| web | 131 | 27 | 2 |
| catalog | 73 | 2 | 2 |
| journey | 73 | 2 | 2 |
| importer | 73 | 2 | 2 |

These are scanner matches, not a claim that every finding is reachable through
this application. The original Web scan reported 264 high/46 critical matches;
the runtime update reduces that to 131/27 and fixes reviewed distro issues.
The three Python images changed from 77 high/3 critical to 73/2 each.
Current Bookworm and Trixie candidates were inspected/scanned. Debian confirms
some Bookworm findings have no distro fix, while some generic binary/CPE matches
do not reflect distro backports. No broad CVE allowlist is introduced.
See [the primary-source review](P10_IMAGE_REVIEW.md) and [ADR 0006](adr/0006-runtime-base-security-update.md).

ADR 0005 requires scanning/review/relevant fixes, not a zero-findings rule.
The locally implemented strict threshold remains failed and visible. The local
implementation can be demonstrated, but images must not be represented as
clean-scan-approved or published without the separate P15 remediation/review decision.
No remote image/data release or public application access occurred.

## Exact prepared release record

- Source: `d6d7752157edad63394b64b83ce0510576105f49`; built once from a clean commit (`source_dirty=false`) after the stable local-link fix.
- Release: `local-d6d7752157ed`.
- Created UTC: `2026-10-20T19:38:00.912906+00:00`.
- Dataset: `gcns-edr3-20261013-20271720`.
- Raw SHA-256: `20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94`.
- Compatibility: Catalog schema 1, Journey schema 1, `constant-speed-v1`.
- No signer identity, SBOM hash, remote registry URL or verification result is invented.

| Image | Actual local OCI manifest digest |
|---|---|
| web | `sha256:03a10a8aca8e1d89600dcf249a6d014564a5e19e70325025e5863ad1619ccc4d` |
| catalog | `sha256:f00d98fa5b1f42ddfdb2fd8276c561272cae411bfe5256961f0ac37bfd77d3ad` |
| journey | `sha256:d662f9dace9f19418d95a62a7dae4ae203b8f728b92feaa508547daeacf0070b` |
| importer | `sha256:4f372b6940490e23e5b393c0829a1668610692b47677bcdcd46bdb2fac55274a` |

Docker on this host returns the same immutable value for the local image ID
and OCI descriptor digest. These references are usable locally; they are not
anonymous GHCR artifacts. The exact runtime record is ignored `.local/release.json`
and served by `/release.json`; Web has the baked `/version.json` source SHA.
The release-source commit is intentionally distinct from later report/test-only
commits and the PR merge commit. The earlier 96a6c03 clean build was superseded
only because final review found the saved-link bug; the corrected application
was rebuilt from the clean commit above.

## Commands and local evidence

```powershell
python tools/run.py dev-up --no-build --json
# http://127.0.0.1:8080/explore
python tools/run.py smoke --target local --json
python tools/run.py images-check --json
python tools/run.py security --json  # expected failure while recorded image findings remain
python tools/run.py dev-down --json  # preserves the named volume
```

For a new clone, follow README bootstrap, supply the preserved/separately acquired
verified P03 asset and run dev-up. A new source build uses dev-up or clean-commit
images-build; --no-build intentionally retains the exact prepared image set.
See [P08](P08_WEB.md), [P09](P09_COMPOSE.md), [P10](P10_CHECKS.md), [P11](P11_RELEASE_IMAGES.md).

Detailed local evidence: `.local/reports/batch3-final-quality.json`,
`db-check.json`, `p09-fresh-compose.json`, `p11-clean-build-final.json`,
`p11-images-final.json`, `p11-persistence.json`, `p11-security-final.json`,
`image-scans/`, `web-review/` and `atlas-interactions.json`.
Credentials, raw data, archives, binary chunks, DB state and these detailed reports
remain ignored. Scientific full-data counts/chunks/checksums reuse Batch 2 evidence;
P09 additionally proved the packaged full import from a fresh volume.

## Resolved failures, human actions and remaining limits

Initial count assertions needed child-text/locale corrections; the pinned generator
needed its optional --array-length flag removed to avoid nested position tuples.
Nginx regex quoting and a closing brace were corrected before startup passed.
A screenshot URL-encoding mistake was corrected; only its own accidental files
were moved back and its empty directories removed. The saved-list index link bug was fixed with a stable calculation key and a real two-journey regression. Windows documentation encoding was corrected before merge; a GitHub CLI description-edit scope error was resolved through the existing permitted REST API, without changing account scopes. No unresolved product/test
failure is hidden. The image threshold failure remains explicitly unresolved.

Existing Git Credential Manager authentication was reused only in child-process
memory. **No login, MFA, paid service or account/setup action was needed.** No
global PATH/execution-policy/tool installation change or unrelated container
mutation was made. The remaining image-publication risk decision belongs before
P15 publication; no publication approval is inferred from elapsed time or silence.

P12 has not started: no kind cluster, Terraform platform, Kubernetes manifests,
Argo deployment, public tunnel, remote publication, backup/restore system or
monitoring stack was created in Batch 3. Final P22 usability/performance and P23
submission acceptance remain later work. Optional signing/SBOMs/scanner frameworks
and strict benchmarks were not added.
