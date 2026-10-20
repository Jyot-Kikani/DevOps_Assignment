# Stellar Atlas — Product Requirements Document

Version: 1.2 | Decision date: 18 October 2026 | Course-scope revision: 20 October 2026 | Status: P00–P07 complete; later phases planned

Read with [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). That document specifies the implementation sequence and operational contracts. This document specifies required user-visible behavior and acceptance criteria.

The user-approved [course-scope amendment](adr/0005-course-assignment-scope.md) controls future checks. Use basic reliable demonstrations and focused tests. Advanced hardening is optional; completed code, sealed data and existing CI checks remain intact.

## 1. Purpose and priority

Stellar Atlas is a data-backed, interactive map of the stellar neighborhood around the Sun. Visitors explore measured star positions, inspect catalog measurements, measure interstellar separations, and calculate simplified journey times.

The primary course deliverable is a reproducible and demonstrably secure software delivery process. The application must be complete and usable, but its scope is deliberately bounded so that Docker, Infrastructure as Code, Kubernetes, CI/CD, DevSecOps, local operation, and public access each receive an implemented workflow and recorded evidence.

Priority order:

1. Zero paid-service expenditure and compliance with the course requirements.
2. Reproducible development, tests, infrastructure, deployment, security, recovery, and evidence.
3. Correct handling of real astronomical data and simple calculations.
4. A polished, understandable application matching the established mockup direction.

## 2. Non-negotiable constraints

| ID | Requirement |
|---|---|
| C01 | No AWS, paid hosting, paid database, purchased domain, subscription upgrade, or dependency on expiring credits. |
| C02 | Application compute, persistence, Kubernetes, and monitoring run on an existing local machine. Free GitHub services and a free public tunnel may be used. Existing hardware, internet, and electricity are assumed. |
| C03 | The final application has independently deployed Catalog and Journey backend services, a web frontend, and a containerized import job. |
| C04 | The public link reaches the Kubernetes deployment, not a separate static replica of the frontend. |
| C05 | Normal application operation uses a locally stored, versioned data snapshot; visitors do not depend on live astronomy API calls. |
| C06 | Existing validation files and generated mockups are preserved. Mockups are visual references, not accurate star-position diagrams. |
| C07 | No scientific claims based on unavailable measurements, fabricated star attributes, or the appearance of generated artwork. |
| C08 | The implementing agent must finish the operational demonstrations and handoff, not stop when the UI builds. |

## 3. Users and principal journeys

| User | Need | Required journey |
|---|---|---|
| Curious visitor | Understand what is near the Sun | Open atlas, change distance radius, select a star, inspect properties. |
| Student | Compare objects and distances | Search for an object, select a second object, inspect a measured separation and assumptions. |
| Explorer | Understand interstellar travel scales | Select origin/destination, change speed, view travel time, play an illustrative journey. |
| Returning visitor | Revisit discoveries | Save stars/journeys locally and reopen them. |
| Evaluator | Verify the entire DevOps process | Open public link, inspect running version, witness pipeline/security/recovery demonstrations. |
| Maintainer | Operate the application reliably | Start the environment, import data, deploy, monitor, back up, restore, and stop it using the runbook. |

### J01 — Explore

Open `/explore`. Load the 50-light-year neighborhood with the Sun highlighted. Rotate and zoom the view, change radius, toggle labels/reference plane/rings, select a star, and return the camera to the Sun. The selected object is reflected in the URL.

### J02 — Inspect and measure

Search by exact catalog ID or curated name. Select a result and inspect distance, available magnitudes, color index, uncertainty, identifiers, source, and epoch. Select another object to measure their three-dimensional separation. Unknown values display `Not available`.

### J03 — Plan and share

Open `/journeys`. Choose an origin and destination, set speed, calculate a constant-speed journey, and use play/pause/scrub controls to illustrate progress. Copy a share URL. Opening that URL reconstructs the persisted journey and its frozen calculation assumptions.

### J04 — Save

Bookmark a star or save a journey in this browser. Open `/saved`, revisit an item, remove an individual saved item, or clear local saved items after explicit UI confirmation. No sign-in is required and the UI explains that saved lists do not sync across devices.

## 4. Data and scientific presentation

### 4.1 Approved dataset

Use the existing GCNS/Gaia EDR3 selected-field snapshot in `validation/gcns_required_fields.csv` as the baseline input. On 18 October 2026 its bytes were independently rehashed:

- Size: 50,104,120 bytes.
- SHA-256: `20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94`.
- Records: 331,312 candidate objects.
- Records with finite X/Y/Z: 331,312.
- Records whose median radius is at most 100 pc: 300,526.
- Objects within 50 ly: 1,151; within 25 ly: 142.

These are properties of the saved snapshot, not promises about a future remote query. Source metadata and original probe outputs already exist under `validation/`.

The GAVO table supplies Galactic Cartesian positions in parsecs and distance percentiles in kiloparsecs. Use its published distance estimates rather than naively inverting parallax. The original INAF CSV has a different schema and does not supply the same ready-made X/Y/Z fields.

Sources: [GCNS service and schema](https://dc.g-vo.org/gcns/q/cone/info), [GCNS paper](https://arxiv.org/abs/2012.02061), [INAF catalog project](https://gucds.inaf.it/projects/gcns/).

### 4.2 Required interpretation

- Coordinates represent the catalog reference epoch, J2016.0. The map is a published-data view, not a live telemetry feed.
- The default map is Sun-centered. The Sun is a special application object at the origin, not an invented Gaia row.
- The catalog is probabilistic and incomplete. Some candidates lie beyond a median distance of 100 pc; the principal map caps its radius at 100 pc.
- Real positions determine placement. Point sizes are enlarged for visibility; photometric color styling is approximate.
- BP−RP increases toward redder colors. It is not presented as a temperature measurement.
- Full physical star radius, mass, temperature, spectral classification, habitability, planets, and photographic surfaces are not inferred from this snapshot.
- A changed camera position does not simulate stellar evolution, light-cone effects, aberration, or a scientifically complete sky image.
- The hypothetical journey assumes a straight path at constant speed in the Sun/catalog frame. It excludes acceleration, gravity, relativity, and spacecraft engineering.
- Public scientific data must retain its source, citation, applicable data-license notice, and transformation history. Software licensing must not relabel the dataset as MIT-licensed.

ESA's current [Gaia data-license page](https://www.cosmos.esa.int/web/gaia-users/license), fetched successfully during planning, specifies **CC BY-NC 3.0 IGO**. This project is educational/noncommercial: retain attribution, license link and change notices, and do not add advertising, commercial reuse or paid data access. Apply the [Gaia EDR3 credit/citation instructions](https://gea.esac.esa.int/archive/documentation/GEDR3/Miscellaneous/sec_credit_and_citation_instructions/) and cite the GCNS paper for the derived catalog.

## 5. Functional requirements

All requirements in this section are required for the final submission. There is no post-submission feature backlog in this plan.

| ID | Requirement and acceptance condition |
|---|---|
| FR01 | **3D atlas:** render actual snapshot coordinates, provide orbit/zoom controls, Sun marker, orientation indicator, scale, and return-home control. No fabricated nebula or planetary orbit layout. |
| FR02 | **Distance selection:** presets 25, 50, 100, 200, and 326.16 ly, with the final preset internally using exactly 100 pc. Show the exact count of matching catalog objects, excluding the synthetic Sun. |
| FR03 | **Map layers:** independently toggle reference plane, distance rings, and labels. Preserve settings during a session and in shareable view links. |
| FR04 | **Selection:** clicking a point selects the appropriate object; selection remains visible when labels are off. Dense views must not create thousands of HTML labels. |
| FR05 | **Search:** debounced search for catalog IDs and curated aliases; keyboard navigation; clear empty/error states; maximum 20 results. Include only names whose source-ID mapping has been checked and recorded. |
| FR06 | **Profile:** show identifier, verified name if present, distance in ly/pc, available G/BP/RP magnitudes, BP−RP, 16th/50th/84th distance percentiles, catalog version, reference epoch, and source links. |
| FR07 | **Neighbors:** show the five closest catalog objects to the selected object within the loaded Sun-centered neighborhood, with separation explicitly labeled as distance from the selected object. Never label their Sun distances as neighbor separations. |
| FR08 | **Distance tool:** select two different objects, draw a straight measurement line, and show their three-dimensional separation in ly and pc. Values agree with server calculations within display-rounding tolerance. |
| FR09 | **Journey calculator:** origin/destination selectors include the Sun; speed range 0.001c–0.5c; default 0.1c. Show distance, speed in c and km/s, and travel time in Julian years. Reject identical endpoints and invalid speeds. |
| FR10 | **Playback:** play, pause, restart, and scrub a journey. Playback duration is 20 real seconds by default, clearly labeled as illustrative. Camera controls remain available. |
| FR11 | **Share journeys:** create an immutable public journey record with an unguessable identifier. Shared records contain only chosen objects and calculation data, not user identity. Explain their 30-day retention before creation. |
| FR12 | **Share views:** copy URL state for selected snapshot/object, radius, layers, camera/target, and observer. Validate untrusted URL values and use safe defaults for invalid state. |
| FR13 | **Saved items:** local-only bookmarks and journey lists; deduplicate; cap at 100 stars and 50 journeys; handle unavailable localStorage. No accounts, cookies for tracking, or cross-device promises. |
| FR14 | **Observer viewpoint:** move the camera near a selected star and show the changed geometry. Keep the Sun-centered catalog-radius filter and explicitly state that brightness is illustrative in this mode. |
| FR15 | **Resilience:** visible loading/progress, empty filters, unsupported WebGL, offline services, failed search, unavailable shared journey, expired journey, and retry states. A searchable list remains usable when 3D rendering is unavailable. |
| FR16 | **Release/data information:** About panel includes source commit, application release, dataset checksum/version/epoch, data attribution, scientific limits, and operating-hours limitation. |
| FR17 | **Responsive/accessibility:** usable desktop atlas and mobile list/detail/journey layout, keyboard-operable controls, focus states, sufficient contrast, reduced-motion support, and text alternatives to color-only meaning. |

## 6. Interface specification

Reference files: `design/mockups/01-explore.png`, `02-star-profile.png`, `03-journey-planner.png`.

- Top navigation: Explore, Journeys, Saved, About; persistent search on desktop.
- `/explore`: filters/list at left, map in the main area, selected-object inspector at right. At narrow widths use a bottom sheet and a list/map toggle.
- `/journeys`: input/result panel and map, with playback controls beneath the map.
- `/saved`: compact cards/rows that reopen a star or journey, with remove controls and empty state.
- `/about`: product explanation, data provenance, attribution/license notices, simplifications, release identifiers, and public-host availability.
- Desktop reference sizes: 1440×900 and 1920×1080. Mobile acceptance size: 390×844. No horizontal page overflow.
- Colors: background `#080d18`, panels `#101925`, active cyan `#58cfe5`, warm amber Sun, off-white body text. Use local/system fonts, no paid assets or external font requests.
- Initial opening animation is at most one second; no continuous automatic camera rotation. Respect reduced motion.
- Display rounded values while retaining float64 calculations. The real catalog's Proxima distance is approximately 4.2464 ly; do not substitute the mockup's rounded labels into the database.

## 7. Non-functional requirements and verification targets

| ID | Target | Measurement |
|---|---|---|
| NF01 | No paid-service dependency | Cost/configuration audit and account-plan screenshots with sensitive fields excluded. |
| NF02 | Local reproducibility | Repeat documented startup successfully with declared prerequisites; check one clean clone at final handoff if practical. |
| NF03 | Responsiveness | Record a simple initial 50-ly load timing and address visibly poor usability. The original 5 s target is advisory; record public-path behavior separately. |
| NF04 | Rendering | Demonstrate usable orbit/selection on the reference laptop and record browser/hardware. The original 30 FPS benchmark is optional. |
| NF05 | API behavior | Demonstrate working API reads/estimates and note obvious delays. The original p95 <500 ms, 10-client/60-second load benchmark is optional. |
| NF06 | Transfer size | No raw CSV in browser responses. Default map binary plus metadata below 1 MiB compressed. Complete in-scope binary assets below 12 MiB compressed. |
| NF07 | Safety | No committed credentials; no public database, Kubernetes administration, Argo CD UI, Grafana, metrics, importer, or migration endpoint. |
| NF08 | Recovery | Demonstrate replacement of one deleted stateless pod and one Git rollback; record elapsed time. Original 120 s/10 min targets are advisory. |
| NF09 | Data resilience | Invalid candidates cannot replace the active catalog. Preserve a working snapshot during import failure. |
| NF10 | Persistence | Restarting pods preserves data. Create a host-stored backup and restore it once to an isolated target, checking catalog count and a journey. Destructive cluster deletion/rebuild is optional. |
| NF11 | Journey retention | Shared journeys expire after 30 days; after expiry return 410 for 7 days, then purge. Saved local journeys retain enough frozen calculation data to display their summary. |
| NF12 | Honest availability | Public availability is conditional on the local host, Docker, Kubernetes, tunnel, and internet. No 24/7 or high-availability claim. |

NF03–NF05 require simple usability observations; their original numeric benchmarks are advisory, not submission gates. NF06 transfer limits remain required. Record actual results and any material usability problems; never label unrun checks as passed.

## 8. DevOps acceptance requirements

| ID | Topic | Mandatory evidence |
|---|---|---|
| DV01 | Microservices | Separate contracts/images/deployments; Journey calls Catalog over HTTP; independent deployment/recovery demonstration; database grants prevent cross-service writes. |
| DV02 | Docker | Reproducible Compose startup, non-root application images, health checks, pinned bases, and image digests. |
| DV03 | IaC | kind configuration plus Terraform-managed platform; first apply, second no-change plan and one detected/restored label drift. A full rebuild is optional. |
| DV04 | Kubernetes | Running services, probes, limits, rollout, pod replacement, Git-managed replica change, persistent data. Custom CNI/network-policy enforcement is optional. |
| DV05 | CI/CD | Protected-main PR checks, failed test gate, successful image build/scan/publish, GitOps promotion, running version verification, and Git rollback. |
| DV06 | DevSecOps | Keep existing secret checks; one Grype image scan, one safe rejected example, non-root app images and private admin surfaces. Signing/SBOMs, extra scanners and attack matrices are optional. |
| DV07 | Local deployment | Documented zero-cost host prerequisites, start/stop commands, resource budget, persistence, monitoring, backup, restore. |
| DV08 | Public URL | External unauthenticated browser reaches the local Kubernetes application over HTTPS through accountless Cloudflare Quick Tunnel. Record the actual temporary URL, update shared links after each new tunnel, and disclose local-host availability and no uptime guarantee. |

## 9. Explicit exclusions

Excluded from this release: user registration, social features, personal data, AI generation, orbital/gravity simulation, whole-galaxy reconstruction, scientifically accurate apparent sky brightness from arbitrary locations, interstellar route optimization, paid domains, cloud compute, managed databases, service mesh, multi-host HA, and a staging cloud environment.

Use CI fixtures and the local demo cluster. Disposable clusters in CI, a custom CNI, signing/SBOM tooling, exhaustive fault matrices and automated disaster recovery are outside the default course scope. Exclusions prevent unrelated scope growth; they are not missing implementation decisions.

## 10. Definition of complete

The release is complete when FR01–FR17, NF01–NF12 and DV01–DV08 have course-sized acceptance evidence under ADR 0005. Focused automated checks and recorded manual demonstrations are both valid; reuse unchanged earlier evidence. The runbook must cover setup, routine startup/shutdown, public access, release, rollback, import, backup, restore, common failures, and guarded teardown. The repository must contain a final architecture diagram, dependency/data attribution, actual measurements, a course-topic evidence matrix, and an assessment script.

Any unmet required behavior is recorded as failed or blocked with its concrete cause. Unselected optional checks are recorded as optional, not failed. A polished mockup, passing build, or planned demonstration is not completion evidence.

