# P14 — Monitoring and manual recovery

```powershell
python tools/run.py monitoring-up --json
python tools/run.py monitoring-check --json
python tools/run.py backup --json
python tools/run.py restore --target restore-check --json
```

Runtime Terraform adds pinned Prometheus 3.15.0 and Grafana 13.2.4 in
`stellar-monitoring`, each with probes, requests/limits and a private ClusterIP.
`monitoring-up` saves the enabled setting beneath `.local/terraform/runtime` so
subsequent platform plans preserve it. Both roots still produce no-change plans.
Prometheus scrapes the two existing API `/metrics` endpoints every five seconds.
Grafana provisions the Prometheus datasource and four panels: availability,
request counts/status, p95 request duration and database failures. No exporter,
alerting suite or dashboard account is required. The generated Grafana admin
password is reused privately from `.local/secrets/grafana_admin`.
Healthy services show zero database failures. Configuration checksum annotations
roll the monitoring pods when their provisioned files change.

`monitoring-check` creates a gateway request, waits for its counter to rise,
requires both scrape targets up, and verifies the four-panel dashboard through
the authenticated Grafana API. Its temporary loopback port-forwards are closed
on exit. To view the dashboard manually, keep these commands running in separate
normal PowerShell terminals (Ctrl+C closes only the forward):

```powershell
.local/tools/kubectl/1.35.8/kubectl.exe --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo -n stellar-monitoring port-forward service/prometheus 9090:9090 --address=127.0.0.1
.local/tools/kubectl/1.35.8/kubectl.exe --kubeconfig .local/kubernetes/config --context kind-stellar-atlas-demo -n stellar-monitoring port-forward service/grafana 3000:3000 --address=127.0.0.1
```

Open `http://127.0.0.1:9090` or `http://127.0.0.1:3000/d/stellar-atlas`.
Log in as `admin` using the private local password file, without printing or
including it in screenshots. Metrics and dashboard data are ephemeral across
monitoring pod recreation; this is a small demo, not a durable monitoring service.
Prometheus keeps at most 24 hours. Monitoring is not exposed by the web gateway.

`backup` creates a real shared journey, records its exact database-row hash,
active snapshot and catalog count, then streams both custom-format `pg_dump`
archives to a unique host directory beneath `.local/backups`. Binary data is
transferred through Python pipes, never PowerShell text redirection. The directory
has current-user-only access and includes SHA-256 hashes, the recovery sample and
actual release identity. Dumps are sequential, not an atomic cross-database
snapshot. The Catalog is immutable; avoid writes while taking a course demo backup.
Role passwords are never dumped; this archive is not a full host or role backup.

`restore --target restore-check` accepts only the latest local backup and creates
a unique `stellar-restore-*` namespace with an isolated PostgreSQL/emptyDir target.
It verifies archive hashes and uses `pg_restore --no-owner --no-privileges
--exit-on-error`. It compares the restored catalog count, active snapshot and
exact saved-journey row hash, then verifies the original gateway/journey still
work. It removes only its unique namespace after the demonstration, preserving
the working PVC and host archives. This proves data recovery; production role
bootstrap/grants and application reconnection are separate steps for a real rebuild.
No restore into the working namespace, scheduled backup or RPO/RTO claim is provided.

Reports: `.local/reports/monitoring-check.json`, `backup.json`, `restore.json`.
See [Batch 4](BATCH4_REPORT.md) for actual validation and selected visual evidence.
Reference: [Prometheus configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/).
