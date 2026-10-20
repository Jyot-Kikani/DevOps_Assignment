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

Final clean-source scan at `96a6c03e5b357d6eb4947d5c4021e6bb46ee62de`:

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
