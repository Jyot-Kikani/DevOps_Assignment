# P21 — Student operating and recovery guide

Run commands in normal PowerShell from this repository. Use the existing Windows
host, Docker Desktop/Linux containers and frozen local tools. The topology is one
kind node, one PostgreSQL PVC and one replica per app normally; monitoring and
Argo are private. Prerequisites/resource budget and installation are in
[README](../README.md) and [P00](P00_PREREQUISITES.md). Preserve `.local/`, the
node container, sealed data and original validation/mockups between demonstrations.

## Routine startup and safe shutdown

Start Docker Desktop first, then use the retained, already provisioned node:

```powershell
python tools/run.py demo-start --json
python tools/run.py smoke --target public --json
# Finish the demonstration:
python tools/run.py demo-stop --json
```

`demo-stop` records a real journey/body/row hash, catalog count/active snapshot and
PVC identity, stops only the recorded project tunnel, then requests a stop of
`stellar-atlas-demo-control-plane` with a 60-second Docker grace period. The
container, PVC, host backups and unrelated `devsecops-demo` remain present. Repeated
stop preserves its checkpoint. It does not delete resources or switch Argo ownership.
The observed kind node exited 137 after that grace period; this was not a clean
PostgreSQL shutdown claim. The subsequent persistence check verifies actual recovery;
host dumps remain the recovery evidence for node/PVC loss.
Private forwards managed by check commands close on exit; close any manually opened
forward terminals with Ctrl+C when finished.

`demo-start` validates the exact node ID when a checkpoint exists, locked image,
kind labels and loopback ports before starting the same container. It waits for the
API, DNS, PostgreSQL, Argo and app rollouts, then checks persistence and current
GitOps source/digests. A successful cycle is archived in `.local/reports/demo-cycle.json`.
It resumes the public tunnel if one was active at stop; without a checkpoint,
startup opens a tunnel by default. `--local-only` suppresses that public start.
An already running start checks the deployment again; it does not recreate/import
the catalog. Failed startup keeps the checkpoint for diagnosis/retry.

Open `http://127.0.0.1:8080/explore` locally. Copy the new temporary HTTPS URL from
the command report or `.local/public/state.json`; rebuild share/view URLs using the
new hostname. The old URL becomes invalid after tunnel stop. A loaded browser may
retain already loaded data, but fresh API requests fail while the host node is
stopped. After startup use Retry/reload. There is no offline server or 24/7 promise.

These commands require an **existing** initialized GitOps cluster. For a first
checkout, follow README bootstrap, [P12](P12_KUBERNETES.md),
[P13](P13_LOCAL_DEPLOYMENT.md), [P15](P15_PUBLICATION.md) and [P17](P17_GITOPS.md)
in order. Do not run first-time setup to repair a routine stop, and do not apply
`demo-bootstrap` after Argo owns the app. The bounded clean-clone source/lock/CLI
review and final handoff are recorded in [Batch 7](BATCH7_REPORT.md).

## Update, rollback and public route

Use a `codex/` source branch and PR. Wait for both current-head required CI jobs
and an up-to-date branch, then merge. Main CI triggers the trusted image
build/Grype/publish/deploy workflow; monitor its result and run `gitops-check`
and public smoke. Documentation-only commits preserve deploy. Grype's strict
threshold remains failed as documented; no clean-scan assertion follows from CI.

For application rollback, follow [P18](P18_UPDATE_ROLLBACK.md): revert exactly
the intended deployment commit on current deploy with a normal Git commit/push,
then verify Argo and public smoke. Preserve database/schema and newer deploy work.
Do not force-push, restore a working DB or use rollout undo against Argo self-heal.

To refresh only the public route while the node stays up:

```powershell
python tools/run.py public-stop --json
python tools/run.py public-start --json
python tools/run.py smoke --target public --json
```

Only Web is tunneled. Argo, Grafana, Kubernetes administration and PostgreSQL
remain private. Existing external-phone evidence is in Batch 5; a new same-host
HTTP/browser check does not claim a new external-device observation.

## Backup, restore, data and monitoring

```powershell
python tools/run.py backup --json
python tools/run.py restore --target restore-check --json
python tools/run.py monitoring-check --json
```

[P14](P14_MONITORING_RECOVERY.md) explains the two host-side custom-format dumps,
checksums, unique isolated restore namespace and sample comparison. Batch 4's
successful restore evidence remains valid because persistence/schema handling is
unchanged. Restore never targets the live DB; it proves dump integrity and isolated
data recovery, not automatic application disaster recovery. Preserve verified
host dumps outside the node before considering a destructive rebuild.

The sealed catalog is already imported. Follow [P05](P05_IMPORT.md) only for an
explicit data operation; do not rerun original validation downloaders. Public data
release, lock and provenance bytes remain unchanged. For a dashboard use P14's
loopback-only forwards. Monitoring counters/history are ephemeral across restart.

## Common observed problems

| Observation | Action |
|---|---|
| Docker/WSL denied in a sandbox | Repeat the inspection in the normal user session; do not reinstall based on sandbox denial. |
| Docker is not running / node absent | Start Docker Desktop and inspect `docker ps -a`. These lifecycle commands deliberately do not create a missing cluster. |
| Port 8080 is busy | Stop only this project's Compose gateway with `dev-down` before kind startup. Inspect the owner; preserve unrelated workloads. |
| Cold GHCR pulls / startup waits | Inspect project pod events and exact digest availability; the earlier cold pull took over ten minutes. Retry after resolution; do not substitute mutable tags. |
| Brief 502/503 after pods start | Gateway endpoint/DNS propagation can lag readiness. Startup waits and retries before comparing the saved journey. |
| Argo is OutOfSync / unhealthy | Inspect the private Application and current deploy revision, resource scope, image pulls and Job status. Run `gitops-check`; do not reapply the manual bootstrap overlay. |
| Tunnel created but DNS/edge is not ready | Inspect `.local/public/cloudflared.log`, retry public smoke shortly, and copy the current hostname. Internet/provider availability remains an external dependency. |
| Saved node/PVC/journey identity differs | Keep the checkpoint and backups; inspect the mismatch. Do not delete state or restore into the live database to conceal it. |
| Grype threshold fails | Preserve the exit code/findings and review [P19](P19_SECURITY_SUMMARY.md); do not lower the threshold or add blanket exclusions. |

This guide intentionally offers no cluster-delete/volume-prune command. A future
destructive teardown/rebuild needs an explicitly named target and verified host
backup. Ordinary shutdown is `demo-stop`. [Batch 6](BATCH6_REPORT.md) records the
tested stop/start. [Batch 7](BATCH7_REPORT.md) records P22 final review, P23
acceptance/handoff and the final observed runtime/public route.
