# P20 — Pod replacement and GitOps scaling

The normal configuration is one replica on one kind node. This demonstrates
controller recovery and replication; it cannot survive loss of the host.

```powershell
python tools/run.py pod-replace --json
```

This deletes exactly one ready Journey pod in `stellar-atlas`, waits for a new
ready UID and gateway recovery, and verifies the same catalog count, active
snapshot, journey HTTP body/database-row hash and Bound PVC. It records observed
elapsed time in `.local/reports/pod-replace.json`. PostgreSQL is not deleted.

For scaling, edit the **current deploy branch**, not the old local bootstrap
overlay. Use a new ignored checkout, preserving the primary source checkout:

```powershell
git clone --single-branch --branch deploy https://github.com/Jyot-Kikani/DevOps_Assignment.git .local/p20-deploy-student
git -C .local/p20-deploy-student switch -c codex/p20-scale
```

In that checkout's `app/app.json`, change only Journey Deployment
`spec.replicas` from 1 to 2. Review the diff, commit it, then push normally:

```powershell
git -C .local/p20-deploy-student add app/app.json
git -C .local/p20-deploy-student commit -m "Demonstrate Journey scaling to two replicas"
git -C .local/p20-deploy-student push origin HEAD:deploy
python tools/run.py gitops-check --json
.local/tools/kubectl/1.35.8/kubectl.exe --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo -n stellar-atlas get deployment,pods -l app=journey -o wide
```

Argo must report Synced/Healthy at the pushed revision, Journey must show 2/2,
and source/release/digests must remain the same. Return to one with
`git -C .local/p20-deploy-student revert --no-edit <your-scale-commit>` and another
normal `push origin HEAD:deploy`. Recheck Argo and 1/1. If deploy moved, stop and
inspect the newer commit; never force-push or revert somebody else's release.
Direct `kubectl scale` is unsuitable here because Argo self-heal restores Git.

The PostgreSQL Deployment mounts `stellar-data/postgres-data`, a 10 GiB RWO PVC
using kind's node-local storage. Pod replacement and retained-node stop/start
preserve it. Container/cluster deletion can destroy its data; a PVC is not a host
backup. [P14](P14_MONITORING_RECOVERY.md) demonstrates host dumps and isolated restore.

Reuse [P18](P18_UPDATE_ROLLBACK.md) for the measured Git rollback and P05/Batch 2
for rejected candidate/atomic activation evidence. [P21](P21_OPERATIONS.md) covers
the offline/resume cycle. [Batch 6](BATCH6_REPORT.md) records actual observations.
