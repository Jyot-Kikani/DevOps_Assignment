# DevOps project demonstration guide

Use [the architecture visualiser](architecture_visualiser.html) for the explanation
and [the file guide](architecture_guide.md) when asked where something is implemented.
This script prioritizes DevOps; keep the application visit to a brief health/identity
check. Allow **12–15 minutes**, with optional operations afterward.

## Before the demonstration

Use normal PowerShell in the repository on the original configured host. Start
Docker Desktop in Linux-container mode. The normal path uses the **retained,
initialized GitOps kind cluster**; it does not install or recreate anything.
First-time setup is a separate process in [README](../README.md) and P12–P17.

```powershell
git status --short --branch
docker ps -a --filter name=stellar-atlas-demo-control-plane
python tools/run.py demo-start --local-only --json
python tools/run.py gitops-check --json
python tools/run.py smoke --target local --json
python tools/run.py monitoring-check --json
```

Expected: commands report `status: passed`, Argo is Synced/Healthy at the current
deploy revision, Web/Catalog/Journey normally have one ready replica each, and
smoke verifies real APIs plus release/data identity. `monitoring-check` verifies
two scrape targets, a rising request counter and the four-panel dashboard.
Some verification commands create a sample journey/request; they are not all
strictly read-only. Keep outputs in `.local/reports/` as the tools already do.

Set a convenient **project-scoped** kubectl command for this PowerShell session:

```powershell
$demoKubectl = Join-Path (Get-Location) '.local/tools/kubectl/1.35.8/kubectl.exe'
function kdemo { & $demoKubectl --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo @args }
kdemo -n stellar-atlas get deployments,pods,services
kdemo -n stellar-data get pvc
```

Keep these ready in browser tabs:

- `docs/architecture_visualiser.html` opened directly from disk.
- [GitHub Actions](https://github.com/Jyot-Kikani/DevOps_Assignment/actions),
  a completed source PR from [Batch 7](BATCH7_REPORT.md), and the
  [deploy branch](https://github.com/Jyot-Kikani/DevOps_Assignment/tree/deploy).
- [Local application](http://127.0.0.1:8080/explore) and its
  [release record](http://127.0.0.1:8080/release.json).
- [P19 security evidence](P19_SECURITY_SUMMARY.md),
  [Batch 6 operations](BATCH6_REPORT.md) and [Batch 4 recovery](BATCH4_REPORT.md).

For private dashboard access, leave each forward running in a separate terminal:

```powershell
# Terminal A
.local/tools/kubectl/1.35.8/kubectl.exe --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo -n stellar-monitoring port-forward service/prometheus 9090:9090 --address=127.0.0.1
```

```powershell
# Terminal B
.local/tools/kubectl/1.35.8/kubectl.exe --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo -n stellar-monitoring port-forward service/grafana 3000:3000 --address=127.0.0.1
```

Open [Prometheus](http://127.0.0.1:9090) and
[Grafana](http://127.0.0.1:3000/d/stellar-atlas). Grafana user is `admin`; enter
the existing local password privately from `.local/secrets/grafana_admin`.
Keep credentials and all Secret/kubeconfig output out of the presentation.
`monitoring-check` closes its own temporary forwards, so these manual forwards
are needed if you want the UI to stay open.

## Main demonstration

### 1. Explain the delivery chain — 1 minute

**Show:** visualiser → “Delivery” → guided steps.

**Say:** “The project runs on my laptop, but delivery is traceable through Git.
A source PR passes quality and secret checks. Successful main CI triggers image
publication and writes the desired application state to a deploy branch.
Local Argo CD pulls that state into Kubernetes.”

Point out that GitHub hosts source/builds/images, Cloudflare supplies access,
and the laptop runs the workloads. No cloud VM or paid cluster is required.

### 2. Show protected source integration — 2 minutes

**Show:** one merged source PR and its checks, then `.github/workflows/ci.yml`.
Use the exact implementation PR/run links in [Batch 7](BATCH7_REPORT.md).

**Say:** “Main requires a PR, an up-to-date branch and both `ci / quality`
and `ci / security`. Quality includes real PostgreSQL integration, browser
flows and four image builds. Security includes pinned-action/lock checks and
full-history Gitleaks. The CI database uses disposable credentials and a small
fixture; it does not connect to my live database.”

**Expected evidence:** successful checks on the PR's final head. For the historical
failed-test gate and safe secret rejection, show recorded Batch 5/P19 evidence.
Do not intentionally break main or introduce a real credential for the presentation.

**Useful distinction:** a PR image build proves packaging, not publication or deployment.

### 3. Follow one release from source to pods — 2 minutes

**Show:** successful `release` Actions run → GHCR packages/digests → deploy branch
`release.json`, `scan-summary.json`, `app/app.json` → `gitops-check` output.
Use the release shown by the live check; a later documentation commit may have
a different SHA while the deployed image stays unchanged.

```powershell
python tools/run.py gitops-check --json
kdemo -n argocd get application stellar-atlas
kdemo -n stellar-atlas get deployments
```

**Say:** “The publisher verifies current main and required checks, builds four
images, scans them, pushes GHCR digests and verifies anonymous access. It writes
generated application manifests to deploy. Argo watches deploy/app and reconciles
the local cluster. Actions has no local kubeconfig. Synced means live desired state
matches Git; Healthy reports resource health. I also run an application smoke test.”

Show source SHA, release ID, image digest and deploy revision as related but
different identifiers. Explain that a digest fixes image content; a tag alone
does not guarantee immutable content.

**Security statement:** “The strict Grype threshold is failed, exit 2. ADR 0005
permits reviewed publication with the findings preserved. This is not a clean
image release.” The final recorded counts are in Batch 7; use the selected
release's actual scan record rather than repeating an older release's counts.

### 4. Show platform ownership and Kubernetes — 2 minutes

**Show:** visualiser → “Platform”, then `infra/kind/cluster.yaml`, the two
Terraform roots and `infra/argocd/application.json`.

```powershell
kdemo get nodes
kdemo -n stellar-atlas get deployments,pods,services
kdemo -n stellar-data get deployments,services,pvc
```

**Say:** “kind creates one Kubernetes node inside Docker. Terraform foundation
owns namespaces, storage and Argo permissions; runtime owns PostgreSQL and
monitoring. Local helpers install Argo and inject credentials separately.
Argo owns application resources. Kubernetes Deployments replace missing pods,
while Services preserve stable routing. Readiness/liveness probes and resource
requests/limits are declared in the manifests.”

Point out Web's NodePort and private ClusterIP services. Explain that PostgreSQL
uses a Deployment plus PVC in this small setup. The 10 GiB PVC survives pod
replacement, but node deletion can destroy the storage.

Optional read-only Terraform demonstration, after checking startup:

```powershell
python tools/run.py platform-plan --root foundation --json
python tools/run.py platform-plan --root runtime --json
```

Expected on an unchanged platform: no changes. The actual drift-detection/repair
exercise is in Batch 4. Do not perform an unreviewed apply just for the presentation.

### 5. Demonstrate controller recovery — 1–2 minutes

This deliberately replaces **one Journey pod**, with a possible brief request
interruption. Run after the initial checks, once the examiner is ready.

```powershell
kdemo -n stellar-atlas get pods -l app=journey -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,READY:.status.containerStatuses[0].ready
python tools/run.py pod-replace --json
kdemo -n stellar-atlas get pods -l app=journey -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,READY:.status.containerStatuses[0].ready
```

**Expected:** new ready pod UID, command reports passed, the same saved sample
and catalog/PVC checks succeed. The helper records observed elapsed time in
`.local/reports/pod-replace.json`; use today's measured time if you run it.
Batch 6's **7.220 s** is historical evidence, not a promised recovery time.

**Say:** “The Deployment/ReplicaSet restores desired replicas; stable service
routing recovers. The pod is replaceable because durable data is stored separately.
This does not prove recovery from laptop or node loss.”

If time is short, show the recorded Batch 6 replacement/scaling result instead.

### 6. Show observability and recovery — 2 minutes

**Show:** visualiser → “Operations”, Prometheus targets and Grafana's four panels.
Use the app briefly to generate requests; refresh the dashboard after a scrape.
Prometheus expression: `up{job="stellar-apis"}`.

**Say:** “Prometheus scrapes both APIs every five seconds. Grafana displays
availability, request/status totals, p95 duration and database failures. This is
basic metrics monitoring; there is no alerting or centralized log stack. Dashboard
history is ephemeral across recreation.”

Then show the **sanitized** backup/restore result in Batch 4 and the commands:

```powershell
# Optional longer operation; creates a fresh sample and host backup.
python tools/run.py backup --json
# Optional: restores the latest backup into a unique isolated target only.
python tools/run.py restore --target restore-check --json
```

**Say:** “A PVC is persistence, not an independent backup. I stream two custom
pg_dump archives to the host, record checksums and verify them with pg_restore
in a unique temporary namespace. It compares catalog state and a saved journey,
then removes only that temporary target. The working database remains in place.”

Reuse existing evidence in the main script. A new isolated restore can take longer;
it is not required on every presentation. The dumps are sequential, not one atomic
cross-database snapshot, and do not implement automated disaster recovery.

### 7. Show controlled public access and close — 1 minute

The preflight intentionally selected local-only. Start a public route explicitly
if you want this segment; it requires internet/provider availability:

```powershell
python tools/run.py public-start --json
python tools/run.py smoke --target public --json
```

Copy the **new URL from this command's output**. Open `/explore` and `/release.json`.
If using a phone, switch to mobile data and test the URL; only describe it as a
fresh external-device check if you actually perform it. Batch 5's earlier phone
test is recorded historical evidence.

**Say:** “cloudflared forwards temporary public HTTPS access to the local Web
gateway at 127.0.0.1:8080. Database, Argo, Kubernetes and monitoring remain private.
The URL changes after restarting the tunnel, and the host must remain on.”

Finish with: “I have demonstrated controlled integration, immutable delivery,
declarative platform/application management, pod recovery, metrics and manual
data recovery. The limits are one host, temporary access and unresolved image
findings.” Keep astronomy/application interaction under a minute overall.

## Optional extended demonstrations

### GitOps scaling, 1 → 2 → 1

Follow [P20's exact separate-checkout procedure](P20_KUBERNETES_OPERATIONS.md).
Change only Journey Deployment replicas in **current deploy `app/app.json`**,
commit/push normally, run `gitops-check` and show 2/2. Revert your scale commit,
push and recheck 1/1. If deploy has moved, inspect the new revision first.

**Talking point:** “Git stores desired replicas. Direct kubectl scaling would
be corrected by Argo self-heal. Two replicas on one node demonstrate replication,
not high availability.” A later source release can overwrite a temporary scale edit.

### Release update and Git rollback

Use [P18](P18_UPDATE_ROLLBACK.md) for a deliberately prepared change. The full
PR/CI/build/pull sequence is too long for the main demo; the actual before/update/
rollback record in Batch 5 is usually better presentation evidence.

The sequence is source PR → passing required checks → merge → publication →
Argo/live verification → normal revert of exactly the intended **deploy commit**
on current deploy → push → Argo/live verification. Preserve newer unrelated
deploy work. Do not force-push or use `kubectl rollout undo` against self-heal.
Application rollback retains the live database/schema. A later main release
can promote current source again.

### Non-root runtime and safe secret rejection

```powershell
kdemo -n stellar-atlas exec deployment/catalog -- id -u
```

Expected for Catalog: `10001`. Show the declared security contexts and private
route checks. The Web Dockerfile and Kubernetes UID settings differ, so do not
generalize this one command to all image users.

Show P19's recorded fake-token rejection; no working token is used. Avoid running
the full `security` command just for this segment: it also rescans images and can
take time/fail the known threshold. Gitleaks' expected fake rejection is exit 1;
Grype's severity-threshold failure is exit 2. Neither means required CI was bypassed.

### Safe stop and resume

```powershell
python tools/run.py demo-stop --json
python tools/run.py demo-start --local-only --json
python tools/run.py gitops-check --json
```

This intentionally makes the application unavailable during the stop. The helper
records a checkpoint and verifies retained node/PVC/sample identity on restart.
It is persistence verification, not a backup. No clean PostgreSQL shutdown is
claimed; the recorded stop required Docker's grace-period termination.

## Questions you are likely to get

| Question | Short answer |
|---|---|
| Why Docker and Kubernetes? | Images package each workload; Kubernetes reconciles replicas, routing, probes, Jobs and storage. Compose remains the earlier local development path. |
| Why Terraform and Argo? | Terraform manages the platform; Argo continuously reconciles application Git state. Their ownership is deliberately separate. |
| Is this continuous deployment? | Successful trusted main checks trigger publication and Git promotion; local Argo auto-syncs. Platform setup and migrations/bootstrap are explicit host operations, not arbitrary CI access to my laptop. |
| Why is a green security check not a clean scan? | The required job checks secrets/publication boundaries. Grype is separately recorded, and its strict image threshold remains failed. |
| What happens if a pod dies? | Kubernetes replaces it; Service routing recovers and the database/PVC are separate. Show actual replacement evidence. |
| What happens if the laptop dies? | Service is unavailable. There is no second host/HA. Host dumps help node/PVC recovery; full-host loss needs a backup copy beyond that failed host, which is not demonstrated here. |
| Does rollback restore the database? | No. Git revert restores application desired state; data restore is a separate isolated verification. |
| Where are secrets? | Protected ignored local files, supplied privately as Kubernetes Secrets outside Terraform/Git. Never show their values. |
| Does Cloudflare host the app? | No. It provides a temporary route to the local gateway. |
| Is Calico / signing / SBOM / ELK used? | Not in the demonstrated scope. Existing pins or vendor files are not implementation evidence. |

## If something fails during the demonstration

| Symptom | Immediate action / explanation |
|---|---|
| Docker/node missing | Start Docker Desktop and inspect the named node. Routine `demo-start` does not create a missing installation. Use recorded evidence instead of improvising a rebuild. |
| Port 8080 occupied | Identify the owner. If it is this project's Compose gateway, `python tools/run.py dev-down --json` preserves its volume. Preserve unrelated workloads. |
| Argo OutOfSync/unhealthy | Inspect current deploy revision and project pod events; cold image pulls can take minutes. Retry checks after resolution; do not rerun old `demo-bootstrap`. |
| Brief 502/503 after replacement/start | Allow endpoint/DNS recovery and retry smoke. Report the actual observed interruption. |
| Public DNS/tunnel failure | Continue locally. Inspect the project tunnel log privately; use `public-stop`/`public-start` if needed, then copy the new URL. |
| Dashboard blank | Keep loopback forward terminals open, create a request and wait for scrape. Use `monitoring-check`; the history is ephemeral. |
| Sandbox denies Docker/WSL | Run the probe in normal user PowerShell. A sandbox denial is not a reason to reinstall. |
| Grype exit 2 | Show findings/review and explain the recorded policy; do not lower thresholds or claim clean images. |

## Finish without deleting the deployment

Close the manual port-forward terminals with Ctrl+C. If you are finished using
the running host, use:

```powershell
python tools/run.py demo-stop --json
```

If keeping the app local but closing public access, use `public-stop --json`
instead. Neither is cluster deletion. Preserve node/PVC, `.local/` and host backups;
there is no need for prune, teardown, reimport or a new cluster during this demo.
