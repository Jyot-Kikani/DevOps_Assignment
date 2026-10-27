# P13 — Local Kubernetes application

Current six-service topology and transition: [service guide](SIX_SERVICES.md),
[ADR 0006](adr/0006-six-application-services.md), [Batch 9](BATCH9_REPORT.md).
Earlier dated validation describes the original two-backend release.

After P12, reuse the clean, prepared P11 release record and images:

```powershell
python tools/run.py demo-bootstrap --json
python tools/run.py smoke --target local --json
python tools/check_kubernetes.py --phase application
# http://127.0.0.1:8080/explore
```

`demo-bootstrap` verifies each Docker image's source/digest against ignored
`.local/release.json`, loads those exact local images into the named kind node,
and verifies its CRI digest references. The rendered manifests use digest image
references with `imagePullPolicy: Never`; nothing is published or pulled from GHCR.
For a new image set, prepare it from a clean commit using `images-build` first.
The P11 record keeps the actual application source SHA even when infrastructure
code advances. Never relabel an old image as built from a newer commit.

`deploy/local/jobs.json` describes ordered bootstrap, Catalog migration, Journey
migration and sealed importer Jobs. Bootstrap receives the existing role secrets;
each later Job receives only its required DSN. No secret values are committed.
The importer verifies the sealed build asset; it does not download/reseal data.
A Job failure stops rollout. Inspect its pod logs in the private normal terminal;
the host helper reports its name and withholds private output. Repeating bootstrap
recreates only these named completed Jobs; migrations/import reuse existing data.

`deploy/local/app.json` contains one Deployment/Service per app, a private DB DNS
alias and the daily 02:00 UTC Journey retention CronJob. Placeholder **values**
are resolved from the actual release at execution; environment variable names
retain their original spelling. Containers have probes, CPU/memory requests and
limits, non-root UID 10001, dropped capabilities and no service-account token.
Catalog receives reader credentials; Journey receives its separate runtime role.
The gateway alone uses NodePort 30080, mapped to host `127.0.0.1:8080`.
PostgreSQL has a separate Terraform-owned Deployment/PVC and no host port.

The application check verifies sealed counts, real Proxima search/calculation,
immutable share/reopen, a Journey workload replacement with the same saved share,
nine gateway private-route denials and one manual execution of the retention Job.
Existing scientific, database role and controlled-clock expiry tests remain valid;
this deployment phase does not repeat their full matrix. Evidence is
`.local/reports/demo-bootstrap.json` and `p13-check.json`.

This is manual local deployment. Argo, deploy-branch promotion, public tunnels,
image/data publication and final scaling/rollback demonstrations remain later phases.
The known failed Grype threshold from Batch 3 remains a recorded limitation.
