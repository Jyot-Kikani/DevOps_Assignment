# P17: local Argo delivery

After P15 public assets/deploy and P16 public checks:

```powershell
python tools/run.py platform-apply --root foundation --json
python tools/run.py gitops-bootstrap --json
python tools/run.py gitops-check --json
python tools/run.py smoke --target public --json
```

Foundation Terraform adds `argocd` and an application-namespace Role/RoleBinding.
The pinned namespace installation/CRDs are verified against the existing lock.
Only controller, repo server, Redis and UI run; unused SSO/ApplicationSet/
notification components are omitted. Platform, database, PVC and monitoring stay
with Terraform. Credentials are never committed or put in Terraform state.

Bootstrap validates the public release and runs the existing ordered idempotent
bootstrap/migration/import Jobs before enabling auto-sync. Existing data stays in
place. The AppProject accepts only the canonical repo and `stellar-atlas`
namespace, with Services, Deployments, ConfigMaps and CronJobs. Argo watches
`deploy/app`, prunes application resources and self-heals. No cluster-admin binding.

`gitops-check` waits for current deploy revision Synced/Healthy, checks deployment
digests and running source/release/data, then calculates/shares a real journey.
It does not call an image push a deployed release. The UI Service is ClusterIP;
for a temporary private UI use the project's kubectl/config/context with
`-n argocd port-forward service/argocd-server 8081:443 --address=127.0.0.1`.
Read the generated initial admin password locally; never log or screenshot it.

Namespace setup follows [Argo's installation guidance](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/).
Do not rerun the old manual `demo-bootstrap` overlay after Argo assumes ownership.
