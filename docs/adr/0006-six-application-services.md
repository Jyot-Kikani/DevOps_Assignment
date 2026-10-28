# ADR 0006 — Split existing features into six backend services

Status: accepted by the user, 28 October 2026.

The user requested six independently deployed backend services for the university
microservices demonstration, using existing functionality. This supersedes the
two-backend topology in the original plan. ADR 0005's small course scope, free
local hosting, scientific rules and existing acceptance behavior remain in force.

## Decision

- **Catalog:** individual stars, ordinals and internal position lookup.
- **Search:** star search and neighbor queries.
- **Atlas Map:** map manifests and immutable compressed binary chunks.
- **Snapshot:** active snapshot and version/provenance metadata.
- **Calculation:** existing constant-speed calculations; requests positions from Catalog over HTTP.
- **Journey:** immutable shared records, idempotency and expiry; requests new calculations over HTTP.

Each has its own package, image, Deployment, ClusterIP Service, health endpoints,
OpenAPI contract and metrics. `atlas_map` is the Python package/directory spelling;
`atlas-map` is the image, Kubernetes and gateway spelling. Web and Importer bring
the release to eight images, but are not counted among the six backend services.

Catalog's read-only query/runtime library is reused by Search, Atlas Map and
Snapshot. These four processes share the existing read-only `catalog_reader`
role and PostgreSQL catalog database. Journey retains its separate database and
runtime role. Calculation receives no database credentials. No database migration
or new third-party dependency is needed. This intentionally small demonstration
does not claim independent data ownership for all six services.

The gateway routes existing browser URLs to the appropriate service. Journey's
existing estimate endpoint remains an HTTP forwarding adapter for internal
compatibility; the public estimate URL routes directly to Calculation. Existing
shares can be read and matching idempotent retries returned without Calculation.

## Delivery and compatibility

The publisher builds/scans all eight images and generates all six backend
Deployments. Argo keeps application ownership; Terraform still manages platform
resources. No platform ownership or public exposure is expanded. Prometheus
configuration includes six private targets.

Old four-image immutable release records remain readable for rollback; partial
six-service image sets are rejected. Existing published manifests are not
rewritten. See [Batch 9](../BATCH9_REPORT.md) for actual checks and delivery state;
source changes alone do not establish that a running deployment has six services.
