# Batch 9 — Six backend microservices

Date: **28 October 2026**. Scope: the user-approved split of existing functionality
into Catalog, Search, Atlas Map, Snapshot, Calculation and Journey. No new product
feature, scientific formula, database migration, data import format or paid service.
Decision: [ADR 0006](adr/0006-six-application-services.md). Usage/service map:
[SIX_SERVICES.md](SIX_SERVICES.md).

## Baseline and changes

Canonical origin remains `Jyot-Kikani/DevOps_Assignment`. Remote main was refreshed
before edits; PR #15 was confirmed merged. Branch `codex/six-microservices` starts
at `e90c417d4397dafff616833f6ba4dea496c1c18c`. The existing local topic-mapping
document is included and updated for the six-service topology.

- Extracted existing read endpoints into Search, Atlas Map and Snapshot API
  packages; Catalog retains star/ordinal/position lookup. The four processes reuse
  the read-only Catalog query/runtime library and existing reader role.
- Moved existing position lookup and scientific calculation into Calculation.
  Journey calls it over HTTP and retains its existing records, idempotency,
  retention and database role. Calculation receives no database credentials.
- Preserved browser URLs through Nginx and Vite routing. Shared wire models retain
  existing input validation and output fields. Public metadata identifies each
  service; private health, metrics and position lookup remain blocked at Nginx.
- Added four non-root image builds and Kubernetes Deployment/Service pairs.
  Releases now contain eight images: six APIs, Web and Importer. Updated rollout,
  smoke/version checks and six-target Prometheus configuration. Terraform and Argo
  retain their existing ownership boundaries.
- Exported service contracts while retaining the combined browser Catalog
  contract. Old four-image release records remain readable for rollback; partial
  sets of extracted service images are rejected.
- Updated current architecture, topic, demo and usage guides. Historical batch
  reports and scientific/validation/mockup inputs are preserved.

## Actual local validation

- Generated contracts/types, locked artifacts, **76 Python unit/contract tests**,
  **five frontend tests**, typecheck, lint and
  frontend build passed. The final Python run is recorded in
  `.local/reports/six-final-python.log`.
- **26 PostgreSQL/integration tests passed**, including six simultaneous HTTP API
  processes with distinct metadata, the Journey → Calculation → Catalog chain,
  binary map gzip/ETag behavior, idempotency, expiry/retention and failure handling.
  Existing shares and matching retries work when Calculation is unavailable.
- **Two real-API Playwright flows passed** against the six fixture-backed APIs:
  atlas/radius/search/selection/measurement, and calculate/illustrate/save/share/reopen.
- **Eight non-root images built** using pinned bases and existing hashed locks.
  CI's importer context is explicitly build-only, not a runnable real-data image.
- **Production Nginx plus all six API images passed** in separate local Compose
  project `stellar-atlas-six-check`. Existing browser routes, all six metadata
  routes, binary delivery and estimate/share/retrieve worked; **21 private routes
  returned 404**. The check was added to the required quality workflow.
- Selected ignored evidence: `.local/reports/six-quality.log`,
  `six-integration.log`, `six-browser.log`, `six-images.log`, `six-gateway.json`
  and per-image build logs in `.local/reports/release/`. Existing warning messages
  about the pinned TestClient dependency and frontend bundle size remain visible.
- Existing scientific/full-catalog/import/backup evidence is reused: no source
  dataset, map encoding, formula or database schema changed. Fixture checks do not
  constitute a fresh full-data Kubernetes demonstration.

## Delivery, runtime and limitations

Implementation: [`f503271`](https://github.com/Jyot-Kikani/DevOps_Assignment/commit/f50327169b6c38e94db2a5c902f6fa20b2a37aea).
Review: [PR #16](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/16).
Local full-history Gitleaks, locked artifacts, pinned actions and publication
boundaries passed after the implementation commit. Required `ci / quality` and
`ci / security` are running on the PR; their
[current-head results](https://github.com/Jyot-Kikani/DevOps_Assignment/pull/16/checks)
are authoritative. No merge, publication or protection bypass is performed.

No images have been published and the retained Kubernetes deployment has not been
upgraded by this refactor. Existing published manifests/images are unchanged.
The new manifests and monitoring configuration are implemented and locally checked;
six-service kind rollout, Argo sync and six live Prometheus targets remain unverified.
The previous strict Grype findings remain recorded; new image vulnerability
results will come from the existing release scan, not from a clean-scan assumption.

Docker Desktop was started for validation and automatically resumed the two old
kind nodes; both were returned to their stopped state. Temporary API/browser and
gateway-check processes are stopped by their check commands. The test database was also stopped, and final Docker inspection found no
running containers. The fixture API/Vite/gateway test ports were closed; host
ports 8080 and 3000 remain owned by unrelated processes and were left untouched. Node/PVC, stored journeys, host backups and
sealed catalog are preserved. No public tunnel was started.

Human demonstration after publication: let Argo apply the six-service application,
review/apply the runtime Terraform plan for updated Prometheus targets, then use
`gitops-check`, `monitoring-check` and the updated demo guide. Do not run the manual
bootstrap overlay over the Argo-owned application. No additional phase is started.

First publication of the four new GHCR packages may require the repository owner
to enable public package visibility before anonymous manifest/pull verification
can pass. The publisher keeps that verification and will not promote inaccessible
images to the deploy branch.
