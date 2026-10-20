# P08 — Web experience

Implemented Explore, Journeys, Saved and About using the existing typed APIs.
The direct Three.js renderer uses validated gzip binary chunks, three concurrent
fetches, real Galactic coordinates, ordinal picking, bounded labels, orbit/zoom,
layers, observer views and a searchable fallback. Radius counts use the API;
the 326.16 ly preset means exactly 100 pc. Selection, layers, snapshot and camera
state are shareable; URL input receives safe defaults.

Profiles retain missing values, percentiles, verified aliases and source links.
Five neighbors show separation from the selected object. The distance tool and
journey calculator use server float64 results. Playback is opt-in, illustrative
and 20 seconds long. Anonymous public shares explain their 30-day lifetime and
retry with the same idempotency key. Browser saves deduplicate and cap at 100
stars / 50 frozen journey summaries; denied storage is visibly reported.

The pinned generator's `--array-length` flag incorrectly multiplied OpenAPI
prefix-item position tuples into nested tuples. Removing that optional flag
regenerates correct coordinate types without changing either HTTP contract.

Validation: 5 frontend unit tests, lint/typecheck/build and both real-API
Playwright flows passed against the existing full baseline. Explore exercised
the 1,151-object default and 300,526-object 100 pc preset, long-ID search,
keyboard selection and measurement. Journey exercised calculation, play/pause,
local save and persisted share reopening. Supplemental review checked all four
routes at 390×844 without horizontal overflow, local persistence/removal/clear
cancellation, unavailable API and WebGL fallback. A mocked HTTP 410 checked the
expiry UI; real expiry semantics reuse P07's database evidence.

Run `npm --prefix apps/web run test:e2e` against a running local app, with
`STELLAR_BASE_URL` set when it is not port 5173. Browser 156.0.8078.4 uses software
rendering in checks; this is functional evidence, not a hardware/FPS benchmark.
Local screenshots and details are under `.local/reports/web-review/`.

P08 development: `python tools/web_probe.py` starts the private loopback API
probe, then `npm --prefix apps/web run dev` starts Vite. Stop only
`stellar-atlas-web-probe` after use. Complete supported startup is added in P09.
The Vite bundle warning is advisory: about 216 KiB gzip including Three.js.
No new dependency, worker/cache framework, Kubernetes or public app was added.
