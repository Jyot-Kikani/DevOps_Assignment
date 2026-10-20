# P03 sealed dataset and publication boundary

Snapshot `gcns-edr3-20261013-20271720` retains the exact frozen CSV bytes.
The original `validation/` catalog and all prior evidence/mockups are preserved.
`data/snapshot.lock.json` records the original URL, checksum, byte sizes, twelve
columns, units, epoch, paper/license citations, transformation version, counts,
notice hashes and eventual GitHub download URL template. The download date is
known; an exact source download time is deliberately not invented.

The raw file is 50,104,120 bytes. Deterministic gzip is 22,743,798 bytes, SHA-256
`284a83d490d701d7aaff1fb3825d0fc093a56a8ffe1869c5987ccf1f55ce46cf`.
Its header has zero timestamp and no filename. `data-seal` recreates a temporary
candidate each time, then compares against the immutable archive and provenance;
changed bytes under the same version fail rather than overwrite.

The installed importer validator streams every row, checks strict string IDs and
uniqueness, header, finite coordinates/positive ordered distance percentiles and
coordinate norm versus kpc distance at relative tolerance 1e-5. Missing optional
photometry becomes null. Distances used for radius counts/calculations come from
the published Cartesian coordinates. The full result is `data/validation-report.json`:

| Check | Result |
|---|---:|
| Unique catalog rows | 331,312 |
| Within 100 pc | 300,526 |
| Within 50 ly | 1,151 |
| Within 25 ly | 142 |
| Available G magnitude | 330,881 |
| Available BP−RP | 324,310 |
| Ordered distance intervals | 331,312 |

Both allowed aliases have exact SIMBAD identifiers and retrieval hashes in
`aliases.sources.json`. SIMBAD currently labels them Gaia DR3; ESA documents
identical EDR3/DR3 source lists. These exact IDs also exist in the frozen catalog.
No other names or synthetic scientific rows have been added to the baseline.
Official Gaia license and EDR3 credit instructions are archived in `data/provenance/`.
The dataset remains CC BY-NC 3.0 IGO for educational/noncommercial use; original
software MIT does not change its rights.

`data-publish` defaults to ignored local staging. It validates the complete asset
set, reuses identical assets, and rejects changed/extra assets without clobbering.
The explicit P15 `--github --repository <owner>/DevOps_Assignment` path checks a public
personal repo, creates/reuses the exact release, compares GitHub asset digests,
uploads only missing assets and verifies final digests. Login/MFA is never started
by this command. It requires an already usable `gh` credential/environment in P15.
On network/rights/digest failure it exits nonzero and preserves existing assets.
Successful publication writes a separate local resolved lock/URL; the sealed
asset's provenance bytes remain immutable.

Repository amendment (2026-10-20): ADR 0004 supersedes the historical `stellar-atlas`
URL template in the sealed lock. Actual publication uses only `DevOps_Assignment`;
the frozen archive/lock/notice bytes remain unchanged. The user made the existing
repository public on 2026-10-20; data-release availability is a separate P15 gate.

P03 exercised local staging and a fresh loopback HTTP download/extraction with
both archive and raw checksum verification. Actual GitHub publication and a public
application URL remain pending P15/P16. Local HTTP testing is not external availability.

Commands:

```powershell
python tools/run.py data-seal --json
python tools/run.py data-publish --json
.local/venvs/ops/Scripts/python.exe tools/check_sealed_data.py
python tools/run.py test --json
```

Exact evidence is in `.local/reports/phases/P03.json` and
`.local/reports/p03-full-data.json`. No database or cluster writes occur in P03.
