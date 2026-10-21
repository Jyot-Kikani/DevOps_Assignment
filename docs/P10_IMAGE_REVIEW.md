# P10 image scan review

The new strict local command uses pinned Grype 0.120.1 with `--fail-on high`.
It completed successfully as a scanner but returned exit 2 for findings. This is
**not a passing security gate**. Existing required GitHub checks are unchanged.

| Image | High | Critical | Scan exit |
|---|---:|---:|---:|
| web | 264 | 46 | 2 |
| catalog | 77 | 3 | 2 |
| journey | 77 | 3 | 2 |
| importer | 77 | 3 | 2 |

These are scanner match counts, not distinct exploitable application defects.
The original Python 3.13 Bookworm base is still the current upstream tag.
The old Nginx Bookworm image has available package fixes and obsolete Nginx.
Current Python 3.13 and Nginx stable Trixie alternatives were also scanned;
both still fail the unchanged high threshold. The maintained Trixie variants
are selected in ADR 0006 for their real distro fixes and current Nginx, with
application compatibility checks required. No clean-scan claim follows from this.

Representative upstream review:

- [glibc CVE-2026-5450](https://security-tracker.debian.org/tracker/CVE-2026-5450): Bookworm vulnerable, no DSA, classified minor by Debian; Trixie fixed.
- [SQLite CVE-2025-7458](https://security-tracker.debian.org/tracker/CVE-2025-7458): Bookworm vulnerable/no DSA, Trixie fixed. The application uses PostgreSQL and exposes no SQLite or arbitrary-SQL API.
- [OpenSSL CVE-2026-84782](https://security-tracker.debian.org/tracker/CVE-2026-84782): Bookworm security version still affected; Trixie has a distro backport. The app does not configure DTLS.

Generic binary/CPE matches also report upstream versions without necessarily
recognizing distro backports. No broad ignore list or severity downgrade is used.
Full JSON reports and candidate scans remain ignored under `.local/reports/`.

ADR 0005 requires a real scan, review and relevant fixes; it does not prescribe
zero scanner findings. The newly introduced strict local threshold is a separate
implementation choice, not an existing required CI check. Its failed result must
remain visible. No unsafe image, data release or public app is published.

Final clean-source scan at `d6d7752157edad63394b64b83ce0510576105f49`:

| Updated image | High | Critical | Scan exit |
|---|---:|---:|---:|
| web | 131 | 27 | 2 |
| catalog | 73 | 2 | 2 |
| journey | 73 | 2 | 2 |
| importer | 73 | 2 | 2 |

Actual package/non-root/health/source/data checks and the local browser/persistence
flows pass on these images. The strict vulnerability gate still fails. Detailed
per-image reports retain their immutable ID in `.local/reports/image-scans/`.
No zero-findings release-readiness claim is made.

## Batch 5 publication scan (21 October 2026)

The first trusted-main release at `2abd14c22f316c180ff163557b9690f18cfa1704`
rebuilt and scanned all four images with Grype 0.120.1. The strict high threshold
returned **exit 2 for every image**: web **91 High / 17 Critical**; Catalog,
Journey and Importer each **55 High / 0 Critical**. This differs from the older
local scan and does not alter its historical findings.

Review of the actual JSON found no High/Critical match with an available fixed
version: web has 96 `wont-fix` and 12 `not-fixed` matches; each Python image has
54 `wont-fix` and 1 `not-fixed`. These are scanner-provided fix states, not a
finding waiver or independent exploitability determination. Representative
matches concern curl/libcurl, libxml2 and util-linux base packages. Application
dependencies/base locks were preserved; no intentionally vulnerable code was
introduced. Non-root runtime and private-route controls remain in place.

Under ADR 0005, scan/review/documentation allows the educational publication
while the threshold remains failed. Raw reports are retained in release Actions
artifacts for three days and locally under `.local/reports/p15-release-first/`;
`deploy/scan-summary.json` preserves concise counts/policy after artifact expiry.

The P18 scan at `ee68173f6f30c1fc48787ce4a8793bce0035daa3` retained those
counts and added one Critical certifi match in Journey and Importer:
[GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2),
with 2026.10.19 listed as fixed. The advisory's description also states that
2026.10.18 removed all emSign roots and .19 restored unaffected roots. Inspection
of the actual running Journey image found certifi **2026.10.18**, **117** trusted
CAs and **zero emSign roots**, with bundle SHA-256
`d87887200c9a705dccc937b9b83b5e67e47024c4a4b7f9dd15700c72e0f55453`.
Importer uses the same locked certifi distribution; that image's bundle was not
independently inspected. The observed Journey bundle already excludes the roots
in the advisory, so no certificate/trust override or dependency upgrade was made.
The version-range match remains recorded as Critical and the threshold remains
failed. P18 raw reports and the on-image observation are retained locally; this
review does not claim that either image has a passing scan.

## Batch 7 final scan (21 October 2026)

Final source `d44d639309d668ef8f74f41b20b319a9b601d76c`, release
`r39573285891-a1-d44d639309d6`, was freshly built and scanned in
[run 39573285891](https://github.com/Jyot-Kikani/DevOps_Assignment/actions/runs/39573285891).
The exact [deploy scan summary](https://github.com/Jyot-Kikani/DevOps_Assignment/blob/6c5f8e67b3bb92a60ade0b5e4da828bd9a240663/scan-summary.json)
records Web **91 High / 17 Critical**, Catalog **55 High / 0 Critical**,
Journey/Importer each **55 High / 1 Critical**. Every high threshold is still
**failed, exit 2**. The raw artifact is preserved locally in
`.local/reports/batch7-release-artifact/` beyond hosted artifact retention.

The two Python Critical matches are the same certifi advisory described above:
installed version `2026.10.18`, scanner-suggested fix `2026.10.19`. The earlier
P18 bundle inspection is historical; this final image's bundle was not independently
reinspected. No upgrade, trust override or finding waiver was introduced for the
submission. These version matches remain unresolved in the final scan. ADR 0005
allows the scanned/reviewed educational demonstration without a zero-findings
claim. [Batch 7](BATCH7_REPORT.md) records the final runtime and other limitations.
