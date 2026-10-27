# Six-service implementation and demonstration

The user-approved split in [ADR 0006](adr/0006-six-application-services.md) extracts
existing endpoints without adding product features or changing scientific formulas.

| Backend service | Existing responsibility | Source package |
|---|---|---|
| Catalog | Star details, ordinal lookup, internal positions | [`services/catalog`](../services/catalog/) |
| Search | Star search and nearby-star queries | [`services/search`](../services/search/) |
| Atlas Map | Map manifests and gzip binary chunks, preserving hashes and ETags | [`services/atlas_map`](../services/atlas_map/) |
| Snapshot | Active dataset, snapshot metadata and provenance | [`services/snapshot`](../services/snapshot/) |
| Calculation | Distance/travel-time estimates using Catalog positions | [`services/calculation`](../services/calculation/) |
| Journey | Create/read shared records, idempotency, 30-day expiry and retention | [`services/journey`](../services/journey/) |

The frontend/gateway and importer are additional components. There are **six
backend APIs, seven long-running application Deployments including Web, and eight
release images including Importer**. PostgreSQL, Argo and monitoring are supporting
infrastructure, not extra application microservices.

## Connections and data

```text
Browser → Web gateway → Search / Snapshot / Atlas Map / Catalog
                     → Calculation → Catalog
                     → Journey → Calculation → Catalog

Catalog / Search / Atlas Map / Snapshot → existing catalog database (read-only)
Journey                                → existing journey database
Calculation                            → no database
```

Existing `/api/catalog/...` and `/api/journey/...` browser URLs stay unchanged.
Nginx routes by path; the Vite development proxy uses the same service boundaries.
Only version metadata is additionally allowlisted at `/api/<service>/v1/meta`.
Metrics, health endpoints and internal position lookup remain private.

The read services share the existing `stellar_catalog` query library and reader
role. Calculation and Journey share wire models in `stellar_common`, not database
access. Scientific source data, binary layout, units, existing records, browser
Saved storage and journey retention rules are unchanged.

## Show the six services

After the six-service release is deployed, use the `kdemo` helper from
[the demo guide](demo_guide.md):

```powershell
kdemo -n stellar-atlas get 'deployments,pods,services'
```

Point out `catalog`, `search`, `atlas-map`, `snapshot`, `calculation`, and `journey`.
Each backend has one independently replaceable Deployment and stable internal
Service, plus `/health/live`, `/health/ready`, `/v1/meta` and `/metrics`.
Prometheus should show six healthy backend targets after its Terraform-managed
configuration has been updated. An older published release still shows two.

Use the unchanged UI to search, inspect a star, load the map, calculate a journey,
create a share and reopen it. New shares traverse Journey → Calculation → Catalog;
reading an existing share needs only Journey and its database.

## Build, validation and delivery

Existing package setup and `python tools/build_packages.py` build all service
packages. The four extracted services reuse existing hashed dependency locks.
`python tools/run.py test --json` checks generated contracts and unit/frontend
gates. `python tools/run.py db-check --json` includes the six-process HTTP fixture
check, existing database/retention checks and a Calculation-outage share check.
`python tools/check_web_ci.py` exercises the unchanged UI against all six APIs.

The existing Compose `dev-up` path builds eight images and starts six APIs plus
Web. Its importer verifies the preserved dataset; no new download or reseal is
introduced. Stop with `dev-down`, retaining the database volume.

For Kubernetes, use the protected PR/main publication workflow and let Argo
reconcile the new application manifests. Do not run manual `demo-bootstrap` over
an Argo-owned app. Apply the reviewed runtime Terraform plan to update monitoring,
then run `gitops-check` and `monitoring-check`. Routine start/stop preserves the
existing node, PVC and backups. Release records and checks support the previous
two-service deployment during transition/rollback.

Actual validation, PR and deployment status: [Batch 9 report](BATCH9_REPORT.md).
