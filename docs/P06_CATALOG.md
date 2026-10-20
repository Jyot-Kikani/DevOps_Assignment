# P06 Catalog API

Catalog implements all versioned routes in `contracts/catalog.openapi.json`.
The literal `/v1/snapshots/active` route precedes parameter routes. Every feature
query uses a retained ready snapshot. Source IDs remain strings; `sun` is returned
only by explicit detail/ordinal-zero/position requests and never enters counts.
All catalog rows have profiles, including candidates beyond the 100 pc map cap.

Runtime requires `APP_ENV`, the actual `SOURCE_SHA`, `RELEASE_ID` (including
`local-<sha12>` for local checks), `CATALOG_SNAPSHOT_ID` and only the catalog-reader
DSN/file. Settings are validated at startup; database migrations never run there.
Lifespan owns/disposes the pool. Process health remains live on database failure;
readiness checks migration head, an active ready snapshot and the required data.
Demo readiness rejects fixture data. Metadata reports the actual active snapshot
and configured source/release identities without host paths or credentials.

Search ranks exact ID, curated alias prefix, then ID prefix, with stable
distance/ID ordering. Empty search lists nearest objects. Literal `%`/`_` are
escaped. Opaque keyset cursors validate numeric values and bind to the immutable
snapshot, normalized search, radius and page size. Cursor context is hashed to
keep even maximum Unicode queries within the bounded cursor contract.

Profile, ordinal and internal positions routes share the same float64 data.
Neighbors first bound candidates by Sun-centered radius, then sort squared
separation from the selected object with an ID tie-break. Both neighbor separation
and Sun distance are returned explicitly. Radius 326.16 ly selects exactly 100 pc.

Map manifests report an exact SQL count and intersecting complete chunks. Chunk
responses return stored gzip bytes directly, immutable caching and a compressed
SHA ETag. Conditional requests support 304. No CSV or numeric Gaia IDs appear in
binary records. Old chunk/profile URLs continue working after active data changes.
The positions batch remains marked internal; public gateway blocking is P09/P13.

The common HTTP boundary bounds bodies to 4 KiB, validates/replaces request IDs,
returns structured errors, sanitizes dependency failures and writes JSON logs.
Prometheus exposes normalized route labels, version identity, latency, query
failures and checked-out pool connections. Object IDs and arbitrary URL paths
never become metric labels. Metrics and docs remain internal until gateway rules
are implemented; no public app/tunnel is started in this batch.

Validation commands:

```powershell
python tools/build_packages.py
python tools/run.py contracts --check --json
python tools/run.py test --json
python tools/run.py db-check --phase P06 --full --json
python tools/check_catalog_browser.py --install-browser
```

The optional flag restores matching pinned Playwright Chromium under ignored
`.local/playwright`; omit it on repeats. Missing Chromium fails the check.
The check opens a temporary loopback-only diagnostic API listener,
checks native `fetch().arrayBuffer()` length/SHA and long-ID ordinal resolution,
then stops it. It implements no frontend screen. PostgreSQL still has no host port.

Full-data measurements in `.local/reports/p06-full-http.json` use 20 sequential
warm requests per endpoint inside the Linux worker. They establish measured
read behavior, not the P22 ten-client/60-second performance target or public-path
latency. The browser wire report is `.local/reports/p06-browser.json`.
