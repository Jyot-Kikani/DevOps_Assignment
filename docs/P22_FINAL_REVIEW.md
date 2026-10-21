# P22 — Final usability and performance review

Reviewed on 21 October 2026 under ADR 0005 against the real Kubernetes catalog.
The unchanged scientific/backend evidence in Batches 2–6 is reused. This review
found stale About availability wording; Batch 7 updates it to explain the actual
temporary Kubernetes/Quick Tunnel route and changing share-link hostname.

## Observed checks

| Flow | Actual result |
|---|---|
| Desktop Explore | 1440×900: rendered map, keyboard Proxima search/selection, profile and five neighbors; orbit changed the shared camera. No page errors. |
| Counts | 50 ly: **1,151**; 326.16-ly preset internally exactly 100 pc: **300,526**. Both maps finished loading. Synthetic Sun excluded. |
| Layers/view links | Labels and plane toggled off, observer/camera/view URL reopened, settings retained; Return to Sun worked. Invalid radius/object/observer/vectors used safe defaults. Existing layer/point-picking tests are reused. |
| Measurement/journey | Existing two real-API browser tests passed: 3D measurement, calculation, play/pause, stable saved links and immutable share reopening. Sun→Proxima: **4.2463769844 ly**, **42.4637698440 Julian years at 0.1c**. |
| Mobile | 390×844 viewport: search/profile→calculate→save→30-day share→reopen; star and frozen journey survived Saved reload. Explore/Journeys/Saved/About had no horizontal overflow. |
| Resilience | Real empty search; deliberately aborted catalog request showed error and Retry recovered against the real API. Explicit 410 UI fixture showed expiry; backend expiry/grace/purge tests are reused from P07. |
| List/storage/motion | With WebGL disabled, list/profile/calculator remained usable. Denied localStorage warned of page-only saves. Reduced-motion mode did not autoplay. |
| Keyboard/appearance | ArrowDown/Enter selected Proxima; native controls and visible focus styling remain. Desktop/mobile screenshots inspected for readable text, clipping and layout. This is a focused review, not a formal accessibility certification. |

## Measurements and scientific bytes

Windows 11 reference laptop: Intel Core Ultra 7 155H, 22 logical CPUs,
approximately 31.6 GiB RAM (P00 inventory; CPU rechecked). Chromium
**156.0.8078.4**, **SwiftShader software rendering**. Mobile is viewport emulation,
not a physical-phone rendering benchmark.

One warm local reload through the Kubernetes gateway, from navigation until the
default 50-ly map completed: **457 ms**. After one warm-up, single sequential
HTTP observations were profile **19 ms**, search **14 ms**, map manifest **23 ms**.
Orbit/selection completed promptly in this run; automated pointer movement does
not establish physical-device smoothness or FPS. No hardware-acceleration,
30-FPS, p95/500-ms or 10-client load claim is made. The final public-path timing
is recorded separately in the Batch 7 report.

Unchanged P05/P06 full-data evidence: **331,312** stored rows; **37** binary chunks,
**6,286,694 compressed bytes** total. Default intersecting chunk **170,138 bytes**
plus **1,333-byte manifest**, below 1 MiB; all chunks below 12 MiB. Browser gzip,
decoded SHA-256, ordinal and exact-radius correctness passed in Batch 2. No raw
CSV is served to the browser. No dataset/chunk/transfer implementation changed.

## Evidence and limits

Selected actual screenshots: [desktop](evidence/batch7-desktop.png),
[mobile journey](evidence/batch7-mobile-journey.png),
[fallback](evidence/batch7-fallback.png), [error](evidence/batch7-error.png).
These capture source `2abd14c22f316c180ff163557b9690f18cfa1704`; the final
About wording update does not change these flows. Full review JSON and the
one-session review script remain ignored in `.local/reports/p22/` and
`.local/p22-review.mjs`; existing reusable checks are `tools/review_web.mjs`
and `apps/web/tests/e2e/journeys.spec.ts`. Set `PLAYWRIGHT_BROWSERS_PATH` to
the absolute `.local/playwright` path when using the existing local browser cache.

Known limits: one software-rendered browser and emulated mobile size; no new
physical mobile-device, screen-reader or complete accessibility audit. Batches
2/3 supply null photometry, invalid speed/endpoints, saved caps, coordinate basis
and retention evidence. They were not exhaustively repeated. The sealed data,
scientific calculations and original validation/mockups remain unchanged.
