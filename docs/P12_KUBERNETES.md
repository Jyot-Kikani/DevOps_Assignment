# P12 — Small local kind platform

Use the pinned project-local tools and existing Docker Desktop. In the normal
Windows user session, from the repository:

```powershell
# Only needed when the Batch 3 Compose gateway occupies 8080. Preserves its volume.
python tools/run.py dev-down --json
python tools/run.py cluster-create --json
python tools/run.py platform-plan --root foundation --json
python tools/run.py platform-apply --root foundation --json
python tools/run.py cluster-secrets --json
python tools/run.py platform-plan --root runtime --json
python tools/run.py platform-apply --root runtime --json
python tools/check_kubernetes.py --phase platform
```

`infra/kind/cluster.yaml` creates only `stellar-atlas-demo`, one pinned Kubernetes
1.35.8 node using kind 0.33.0, default kind networking and the default `standard`
local-path provisioner. API and gateway mappings bind to loopback. The existing
unrelated cluster is not reused or changed. The kubeconfig is private
`.local/kubernetes/config`; commands always select `kind-stellar-atlas-demo`.
The normal global kubectl context is not changed. An existing cluster is checked
for the expected node image and port mapping; mismatches fail without deletion.

Terraform 1.16.6 uses the existing provider 3.3.0 checksum locks. Foundation owns
the application/data/monitoring namespaces and a 10 GiB PVC. Runtime owns one
PostgreSQL Deployment/ClusterIP Service and, after P14, monitoring. JSON Terraform
configuration (`main.tf.json`) is native Terraform syntax. Both roots use an
explicit local backend and ignored `.local/terraform/<root>` state, plans,
provider data and inputs. No credentials are passed to Terraform. PostgreSQL
credentials and role-specific DSNs come from existing current-user-only files,
applied through kubectl stdin without logging values. Never print Secret YAML.

The focused platform check requires both no-change plans, changes one harmless
namespace label, observes a Terraform diff, repairs it, then requires another
no-change plan. It also checks DB readiness and the storage provisioner. Logs
and the result remain in `.local/terraform/` and `.local/reports/p12-check.json`.
Ordinary labels are not a network-policy demonstration; no Calico is installed.

The PVC uses delayed binding, so it becomes Bound when PostgreSQL is scheduled.
Its Terraform resource has `prevent_destroy`. Pod and Docker Desktop restarts
preserve data, but deleting the kind cluster can destroy the local-path volume.
Do not delete the cluster as a routine stop. Back up to the host first (P14).
There is no destructive teardown helper in this batch. Stop only this node with
`docker stop stellar-atlas-demo-control-plane`; resume it with `docker start
stellar-atlas-demo-control-plane`, wait for readiness, then run smoke. Do not use
Compose startup while kind owns port 8080.

Configuration reference: [kind port mappings](https://kind.sigs.k8s.io/docs/user/configuration/).
Actual results are in [Batch 4](BATCH4_REPORT.md).
