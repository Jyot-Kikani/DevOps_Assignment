# P05 atomic import and map preprocessing

The installed `stellar_importer` package reads local sealed files only. Its
`validate`, `import`, `report`, `smoke` and `retention` CLI actions have explicit
exit codes. `validate-baseline` remains available. There is no import HTTP route.

After P04 bootstrap and a first-party wheel rebuild:

```powershell
python tools/build_packages.py
python tools/run.py db-check --phase P05 --full --json
python tools/run.py catalog-import --json
python tools/run.py catalog-report --json
```

`catalog-import` verifies the preserved baseline and its sealed archive at
`.local/data/sealed/gcns-edr3-20261013-20271720/`, then imports/activates that exact
version. It never downloads or overwrites `validation/`, the seal or notices.
Generic candidate imports use an explicit separately reviewed manifest:

```text
python -m stellar_importer validate <csv> --manifest <lock> --archive <gzip> --aliases <csv> --json
python -m stellar_importer import <csv> --manifest <lock> --archive <gzip> --aliases <csv> --activate --json
python -m stellar_importer report --json
```

These commands run where the designated writer DSN is available. Omit `--activate`
to retain the current pointer. An already-ready older snapshot can be explicitly
activated again. Snapshot identity/provenance conflicts fail instead of replacing
bytes. Ready snapshots are retained indefinitely in this release.

Preflight verifies schema/header/epoch/transformation, compressed/raw hashes and
sizes, manifest counts, strict string IDs, uniqueness, finite coordinates,
positive ordered intervals, units/norm agreement and curated alias hashes. Demo
mode rejects fixture manifests. The frozen baseline has its original provenance;
ADR 0004 still supersedes only its historical future publication URL.

The importer sorts compact tuples by radius and numeric source ID, obtains an
advisory transaction lock, inserts staging metadata and COPYs normalized rows.
It independently reads back every persisted row/ordinal and alias. Only objects
within 100 pc enter 8192-record map chunks; all 331,312 rows retain profiles.
Each chunk stores deterministic gzip bytes, both hashes, sizes and radius/ordinal
bounds. Ordinal zero is reserved for the client-generated Sun.

Counts and chunks are checked before the same transaction marks the snapshot
ready and optionally changes the singleton pointer. Concurrent retry verifies
and reuses existing immutable rows and exact chunk bytes. Transaction rollback
preserves the prior active snapshot after parse, database or process failures.
Failure reports/logs are outside catalog state, under ignored `.local/reports`.

Mandatory CI tests use only the small attributed fixture. The explicit `--full`
gate independently queries SQL counts and rehashes/decompresses every full-data
chunk, records transfer sizes and Linux peak RSS under the 512 MiB worker limit.
`test_full_data.py` is not collected without that flag; a fixture pass never
claims full-catalog verification. Results are saved in
`.local/reports/p05-full-import.json` and `batch2-integration.xml`.

The kill test terminates a separate process after staging COPY writes but before
readiness/activation, proves no candidate rows became visible, then retries
successfully. Other tests cover concurrent activation, exact reuse, explicit
data rollback, immutable-row triggers and invalid candidate rejection.
