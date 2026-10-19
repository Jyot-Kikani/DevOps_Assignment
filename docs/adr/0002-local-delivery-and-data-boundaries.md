# ADR 0002: Local delivery and immutable data boundaries

Status: accepted architecture from PRD/implementation plan, recorded in P01.

Use React/TypeScript/direct Three.js; independently packaged FastAPI Catalog and
Journey services; PostgreSQL 17 with isolated databases/roles; and a containerized
import job. Journey calls Catalog through HTTP and never reads its database.
Browser saved items remain local; shared journeys are anonymous and expire.

Existing hardware runs Compose for development and kind/Calico for demonstration.
Terraform owns the platform, Argo owns application resources, and GitHub Actions
publishes scanned/signed digest-pinned releases. No AWS account, paid hosting,
expiring credit, purchased domain or long-lived self-hosted runner is required.
Public routing uses the accountless Quick Tunnel decision in ADR 0001.

Retain the existing immutable GCNS snapshot and its upstream license/credits.
Keep IDs as strings, calculations as float64 and map buffers as float32. Unknown
photometry remains null. Mockups are visual references, never scientific input.
Raw data and machine state stay out of Git. Provider and runtime integration
claims require their later phase checks.
