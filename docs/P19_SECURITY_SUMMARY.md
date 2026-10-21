# P19 — Basic DevSecOps evidence

This is the limited course demonstration in ADR 0005. See [Batch 6](BATCH6_REPORT.md)
for the observed commands, release and evidence. It is not a clean-image claim.

| Control | Demonstration / evidence |
|---|---|
| Committed secrets and publication boundaries | Existing `python tools/ci_security.py --json`; full Git history, locked tools and pinned actions. Both protected CI jobs remain required. |
| Safe rejection | Existing `stellar_ops.security.fake_rejection()` generates a fake token in process memory and expects Gitleaks exit 1. Its log is redacted; no working credential is introduced. |
| Image vulnerability scan | Reuse the exact running release's Grype 0.120.1 `scan-summary.json` on deploy and the actual Batch 5 scans. The unchanged `--fail-on high` result is **failed, exit 2**. [Image review](P10_IMAGE_REVIEW.md) records findings and limitations. |
| Non-root applications | Live Web/Catalog/Journey `id -u` is 10001; pod templates set `runAsNonRoot`, disable service-account token mounts and specify digest images/probes/limits. Importer image/job settings and runtime checks are recorded in Batches 3/5. |
| Private administration and database | Only Web is a NodePort, mapped to host loopback. PostgreSQL, Argo and monitoring Services are ClusterIP. The tunnel points only to Web; API routing uses an allowlist. Public metrics/docs/admin/import/migration requests return 404. |
| Database role boundaries | Reuse Batch 2's real PostgreSQL role-denial checks and unchanged role-specific Secrets. Credentials stay outside Terraform/Git. |

Read the existing gate's actual exit/status and the fake-rejection result. A successful
control demonstration does not turn the vulnerability threshold into a pass. The
running rollback release has Web **91 High / 17 Critical**, and Catalog/Journey/
Importer each **55 High / 0 Critical** at its scan time. These are scanner matches,
not independently established exploitable application flaws. The newer, rolled-back
image scan and older failed scans remain historical evidence.

Review staged files before commit (`git diff --cached --stat` and the actual diff).
Keep raw logs, credentials, dumps, state and screenshots under ignored `.local/`.
Gitleaks uses redaction; do not print Secret objects, environment variables or
Grafana passwords for evidence. No extra scanner, signing policy, custom CNI or
network-policy claim is added by this phase.
