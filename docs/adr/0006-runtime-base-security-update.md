# ADR 0006 — Update application runtime base variants after real scans

Status: implemented within the authorized P10 security review, 21 October 2026.
Supersedes only the application's Bookworm base-variant selection. Preserves
Python 3.13, Nginx, all dependency versions/contracts, PostgreSQL and P00–P07.

The first real Grype scan found fixable issues in the old Nginx 1.28 Bookworm
image and Bookworm issues without distro updates. Current Bookworm tags were
checked, not assumed stale. Debian confirms glibc CVE-2026-5450 and SQLite
CVE-2025-7458 remain vulnerable on Bookworm and are fixed on Trixie. See
[the scan review](../P10_IMAGE_REVIEW.md) and its primary-source links.

Use digest-pinned official Python 3.13 slim Trixie and upstream unprivileged
Nginx stable Trixie (NGINX 1.30.6). This is a Debian major-version change and
therefore explicitly records the compatibility decision required by the version
policy. It avoids compiling a custom libc/OpenSSL distribution or maintaining
a large scanner exception framework for a course project. Node is build-only;
its existing pinned Bookworm image is unchanged. Historical Bookworm pins remain
for the already verified database maintenance worker, without rewriting evidence.

Equivalent application checks: locked wheel build/install and pip consistency,
non-root execution, explicit migrations and sealed import/reuse, both API health
and identity endpoints, float64 journey smoke, gateway exclusions, two real-data
browser flows and persistence after restart. Run these against the actual new
images before recording success. No scientific transformation changes.

The Trixie candidates still fail the strict Grype high threshold. This change
does not waive findings, lower severity, ignore CVEs, claim zero vulnerabilities
or publish an image. Preserve full scan results and the explicit remaining
limitation. Existing required CI/protected-main rules remain unchanged.
