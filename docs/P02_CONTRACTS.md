# P02 contracts and executable foundation

The two installed service packages export 13 Catalog paths and 7 Journey paths
(including health, metadata and metrics). Every request/response has explicit
types, bounds and shared error envelopes. Feature handlers intentionally return
503 until P06/P07; no data service or database has been deployed.

`contracts/` contains committed OpenAPI, release/phase schemas, public configuration
and the binary format descriptor. Generated TypeScript comes from pinned
`tools/codegen/package-lock.json`. `contracts --check` checks deterministic regeneration.
Cross-field release invariants are also enforced by `tools/schema_models.py`;
JSON Schema alone does not express signer/source/image relationships.

`stellar_common` uses the standard library for IDs, float64 calculations, errors,
redacted logging, 24-byte map encoding and deterministic gzip. Each service/job has
its own wheel project; all four wheels were built and installed into isolated
environments. Tests import those installed wheels, not unmounted sibling sources.

Independent tests cover the 3-4-5 triangle, Sun conversion, one Julian year,
very small and zero distances, speed boundaries, identical endpoint rejection,
nonfinite values, long string IDs, manually encoded binary bytes, null photometry,
gzip determinism, coordinate handedness, request bounds and invalid release metadata.
The five-row catalog fixture has three attributed real rows and two explicitly
synthetic edge cases, with its own checksum/count manifest.

All 37 PRD acceptance IDs are registered as not run in `ACCEPTANCE.md`; passing
these foundation tests does not satisfy whole-feature or deployment acceptance.
Exact commands/results are retained locally in `.local/reports/phases/P02.json`.
