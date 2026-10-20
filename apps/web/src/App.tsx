import { useEffect, useRef, useState } from 'react';
import { Atlas } from './Atlas';
import type { CameraState } from './Atlas';
import { Search } from './Search';
import { catalog, label, number, post, request } from './lib/api';
import type { Estimate, JourneyInput, Manifest, Neighbors, SharedJourney, Snapshot, Star } from './lib/api';
import { addSaved, EMPTY, journeyKey, objectId, RADII, readSaved, readView, viewUrl } from './lib/state';
import type { Saved, View } from './lib/state';

const message = (error: unknown) => error instanceof Error ? error.message : 'Service unavailable. Please retry.';
const starLink = (s: Star) => `/explore?snapshot=${s.snapshot_id}&star=${s.source_id}`;
const params = new URLSearchParams(location.search);

export function App() {
  const page = location.pathname.split('/')[1] || 'explore';
  const [view, setView] = useState(readView);
  const [snapshot, setSnapshot] = useState<Snapshot>();
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [notice, setNotice] = useState('');
  const [saved, setSaved] = useState<Saved>(() => { try { return readSaved(localStorage); } catch { return EMPTY; } });
  useEffect(() => {
    try { readSaved(localStorage); } catch { setNotice('Local storage is unavailable or damaged. Saved items are held only until this page closes.'); }
  }, []);
  useEffect(() => {
    const abort = new AbortController(); setError('');
    request<Snapshot>(view.snapshot ? catalog(view.snapshot) : '/api/catalog/v1/snapshots/active', { signal: abort.signal })
      .then(value => { setSnapshot(value); setView(v => ({ ...v, snapshot: value.snapshot_id })); })
      .catch(e => { if (!abort.signal.aborted) setError(message(e)); });
    return () => abort.abort();
  }, [view.snapshot, attempt]);
  function store(next: Saved) {
    setSaved(next);
    try { localStorage.setItem('stellar-atlas-v1', JSON.stringify(next)); setNotice('Saved in this browser.'); }
    catch { setNotice('Local storage is unavailable. Changes are held only until this page closes.'); }
  }
  function save(item: Star | Estimate) { try { store(addSaved(saved, item)); } catch (e) { setNotice(message(e)); } }
  async function copy(url: string) {
    setNotice(url);
    try { await navigator.clipboard.writeText(url); setNotice(`Link copied: ${url}`); }
    catch { setNotice(`Copy this link: ${url}`); }
  }
  return <><a className="skip" href="#content">Skip to content</a><header>
    <a className="brand" href="/explore"><span aria-hidden="true">✧</span> STELLAR ATLAS</a>
    <nav aria-label="Main navigation">{['explore', 'journeys', 'saved', 'about'].map(name => <a key={name} href={`/${name}`} aria-current={page === name ? 'page' : undefined}>{name[0].toUpperCase() + name.slice(1)}</a>)}</nav>
    <span className="edition">OUR STELLAR NEIGHBORHOOD</span></header>
    {notice && <div className="notice" role="status">{notice}<button aria-label="Dismiss notification" onClick={() => setNotice('')}>×</button></div>}
    <main id="content">{page === 'saved' ? <SavedPage saved={saved} store={store} /> : page === 'about' ? <About snapshot={snapshot} /> :
      page === 'journeys' && (params.has('id') || params.has('local')) ? <Journeys snapshot={snapshot} view={view} save={save} copy={copy} saved={saved} /> :
      error ? <div className="empty" role="alert"><h1>Catalog unavailable</h1><p>{error}</p><button onClick={() => setAttempt(a => a + 1)}>Retry catalog</button></div> : !snapshot ? <p className="empty" role="status">Connecting to the catalog…</p> :
        page === 'journeys' ? <Journeys snapshot={snapshot} view={view} save={save} copy={copy} saved={saved} /> :
          <Explore snapshot={snapshot} view={view} setView={setView} save={save} copy={copy} />}</main>
    <footer>Gaia EDR3 / GCNS · Epoch J2016.0 · Educational, noncommercial · Local-host availability</footer></>;
}

function Explore({ snapshot, view, setView, save, copy }: { snapshot: Snapshot; view: View; setView: React.Dispatch<React.SetStateAction<View>>; save: (item: Star) => void; copy: (url: string) => void }) {
  const [selected, setSelected] = useState<Star>();
  const [neighbors, setNeighbors] = useState<Neighbors>();
  const [error, setError] = useState('');
  const [neighborError, setNeighborError] = useState('');
  const [count, setCount] = useState<number>();
  const [origin, setOrigin] = useState<Star>();
  const [measurement, setMeasurement] = useState<Estimate>();
  const [measurementError, setMeasurementError] = useState('');
  const [mobileMap, setMobileMap] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const cameraRef = useRef<CameraState | undefined>(undefined);
  useEffect(() => { history.replaceState(null, '', viewUrl(view, cameraRef.current)); }, [view]);
  useEffect(() => {
    const abort = new AbortController();
    request<Manifest>(`${catalog(snapshot.snapshot_id)}/map?radius_ly=${view.radius}`, { signal: abort.signal })
      .then(m => setCount(m.total_count)).catch(() => {});
    return () => abort.abort();
  }, [snapshot.snapshot_id, view.radius]);
  useEffect(() => {
    const abort = new AbortController(); setSelected(undefined); setError('');
    request<Star>(`${catalog(snapshot.snapshot_id)}/stars/${view.selected}`, { signal: abort.signal }).then(setSelected).catch(e => { if (!abort.signal.aborted) setError(message(e)); });
    return () => abort.abort();
  }, [snapshot.snapshot_id, view.selected, attempt]);
  // Restore the observer independently of the selected object in shared views.
  useEffect(() => {
    if (view.observer === 'sun' || view.camera) return;
    const abort = new AbortController();
    request<Star>(`${catalog(snapshot.snapshot_id)}/stars/${view.observer}`, { signal: abort.signal }).then(star => {
      setView(v => ({ ...v, selected: star.source_id }));
    }).catch(() => { if (!abort.signal.aborted) setView(v => ({ ...v, observer: 'sun' })); });
    return () => abort.abort();
  }, [snapshot.snapshot_id, view.observer, view.camera, setView]);
  useEffect(() => {
    const abort = new AbortController(); setNeighbors(undefined); setNeighborError('');
    request<Neighbors>(`${catalog(snapshot.snapshot_id)}/stars/${view.selected}/neighbors?radius_ly=${view.radius}&limit=5`, { signal: abort.signal })
      .then(setNeighbors).catch(e => { if (!abort.signal.aborted) setNeighborError(message(e)); });
    return () => abort.abort();
  }, [snapshot.snapshot_id, view.selected, view.radius, attempt]);
  useEffect(() => {
    setMeasurement(undefined); setMeasurementError('');
    if (!origin || !selected || origin.source_id === selected.source_id) return;
    const abort = new AbortController();
    request<Estimate>('/api/journey/v1/estimate', { ...post({ snapshot_id: snapshot.snapshot_id, origin_id: origin.source_id, destination_id: selected.source_id, speed_fraction_c: .1 }), signal: abort.signal })
      .then(setMeasurement).catch(e => { if (!abort.signal.aborted) setMeasurementError(message(e)); });
    return () => abort.abort();
  }, [origin, selected, snapshot.snapshot_id, attempt]);
  function pick(ordinal: number) {
    request<Star>(`${catalog(snapshot.snapshot_id)}/ordinals/${ordinal}`).then(star => setView(v => ({ ...v, selected: star.source_id }))).catch(e => setError(message(e)));
  }
  function home() {
    const extent = view.radius / 3.261563777;
    // Changing radius key is unnecessary: Atlas remount restores this explicit camera.
    cameraRef.current = undefined;
    setView(v => ({ ...v, observer: 'sun', camera: [extent * 1.15, extent * .8, extent * 1.15], target: [0, 0, 0] }));
  }
  return <div className={`workspace ${mobileMap ? 'show-map' : ''}`}>
    <aside className="panel rail"><p className="eyebrow">EXPLORE / REAL CATALOG DATA</p><h1>Our stellar neighborhood</h1><p>Measured positions. A different sense of distance.</p>
      <label>Distance from Sun<select value={view.radius} onChange={e => { setCount(undefined); setView(v => ({ ...v, radius: Number(e.target.value), camera: undefined, target: undefined })); }}>{RADII.map(r => <option key={r} value={r}>{r} light-years{r === 326.16 ? ' (exactly 100 pc)' : ''}</option>)}</select></label>
      <p className="count">{count == null ? 'Loading count…' : `${number(count, 0)} catalog objects`}<small>Sun excluded</small></p>
      {(['labels', 'plane', 'rings'] as const).map(key => <label className="toggle" key={key}><input type="checkbox" checked={view[key]} onChange={e => setView(v => ({ ...v, [key]: e.target.checked }))} />{({ labels: 'Star labels', plane: 'Reference plane', rings: 'Distance rings' })[key]}</label>)}
      <div className="legend" /><small>Bluer ← BP−RP color index → Redder<br />Approximate styling; no temperature inference</small>
      <Search snapshot={snapshot.snapshot_id} radius={view.radius} onSelect={star => setView(v => ({ ...v, selected: star.source_id }))} />
    </aside><section className="map-panel"><div className="map-toolbar"><span>Observer: {view.observer === 'sun' ? 'Sun' : view.observer}</span><button onClick={home}>Return to Sun</button><button onClick={() => copy(viewUrl(view, cameraRef.current).href)}>Share view</button></div>
      <Atlas key={`${view.camera?.join(',')}:${view.target?.join(',')}`} snapshot={snapshot.snapshot_id} view={view} selected={selected} route={measurement} cameraRef={cameraRef} onPick={pick} onCount={setCount} />
      {view.observer !== 'sun' && <p className="map-note">View from a star: brightness is illustrative. The catalog radius remains centered on the Sun.</p>}
      <div className="measurement"><strong>3D distance tool</strong>{origin ? <p>From {label(origin)} → {selected ? label(selected) : 'select another star'}<br />{measurement ? `${number(measurement.distance_ly, 5)} ly · ${number(measurement.distance_pc, 5)} pc` : 'Select a different object to measure.'}</p> : <p>Set a star as the origin, then select a second star.</p>}{measurementError && <p role="alert">{measurementError}<button onClick={() => setAttempt(a => a + 1)}>Retry measurement</button></p>}</div>
    </section><aside className="panel inspector">{error ? <p role="alert">{error}<button onClick={() => setAttempt(a => a + 1)}>Retry profile</button></p> : !selected ? <p role="status">Loading profile…</p> : <>
      <p className="eyebrow">SELECTED OBJECT</p><h2>{label(selected)}</h2><p className="id">{selected.source_id}</p><div className="hero-number">{number(selected.distance_ly, 4)}</div><p>Light-years from Sun</p>
      <dl>{[['Distance estimate', `${number(selected.distance_pc, 6)} pc`], ['G magnitude', number(selected.g_magnitude)], ['BP magnitude', number(selected.bp_magnitude)], ['RP magnitude', number(selected.rp_magnitude)], ['BP−RP', number(selected.color_index)]].map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl>
      <details><summary>Distance uncertainty (16th / 50th / 84th)</summary><p>{number(selected.distance_p16_pc, 6)} / {number(selected.distance_pc, 6)} / {number(selected.distance_p84_pc, 6)} pc</p></details>
      <div className="actions"><button className="primary" onClick={() => setView(v => ({ ...v, observer: selected.source_id, camera: undefined, target: undefined }))}>View from here</button>
        <button onClick={() => save(selected)}>Save star</button><button onClick={() => { setOrigin(selected); setMeasurement(undefined); }}>Set measurement origin</button>
        <a className="button" href={`/journeys?snapshot=${snapshot.snapshot_id}&destination=${selected.source_id}`}>Plan a journey</a></div>
      <h3>Closest within this neighborhood</h3><small>Separation from {label(selected)}</small>{neighborError && <p role="alert">{neighborError}<button onClick={() => setAttempt(a => a + 1)}>Retry neighbors</button></p>}
      {neighbors?.items.map(n => <button className="neighbor" key={n.star.source_id} onClick={() => setView(v => ({ ...v, selected: n.star.source_id }))}>{label(n.star)}<small>{number(n.separation_ly)} ly from selected object</small></button>)}
      {neighbors && !neighbors.items.length && <p>No neighbors in this radius.</p>}
      <p className="id">{snapshot.snapshot_id}<br />Gaia EDR3 / GCNS · J{snapshot.epoch}.0</p><a href={snapshot.source_url} target="_blank" rel="noreferrer">Catalog source ↗</a></>}
    </aside><button className="mobile-switch" onClick={() => setMobileMap(v => !v)}>{mobileMap ? 'Show list and details' : 'Show 3D map'}</button></div>;
}

function Journeys({ snapshot, view, save, copy, saved }: { snapshot?: Snapshot; view: View; save: (item: Estimate) => void; copy: (url: string) => void; saved: Saved }) {
  const snapshotKey = snapshot?.snapshot_id ?? view.snapshot ?? '';
  const [origin, setOrigin] = useState(objectId(params.get('origin')));
  const [destination, setDestination] = useState(objectId(params.get('destination')));
  const [speed, setSpeed] = useState(.1);
  const [result, setResult] = useState<Estimate>();
  const [shared, setShared] = useState<SharedJourney>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [shareUrl, setShareUrl] = useState('');
  const cameraRef = useRef<CameraState | undefined>(undefined);
  const pendingShare = useRef<{ body: string; key: string } | undefined>(undefined);
  const sharedId = params.get('id');
  const localKey = params.get('local');
  const frozen = !!sharedId || localKey != null;
  useEffect(() => {
    const abort = new AbortController(); setError('');
    if (sharedId) {
      if (!/^[a-f0-9-]{36}$/i.test(sharedId)) { setError('Invalid shared journey link.'); return; }
      setBusy(true);
      request<SharedJourney>(`/api/journey/v1/journeys/${sharedId}`, { signal: abort.signal }).then(j => {
        setResult(j); setShared(j); setOrigin(j.origin_id); setDestination(j.destination_id); setSpeed(j.speed_fraction_c);
      }).catch(e => { if (!abort.signal.aborted) setError(message(e)); }).finally(() => { if (!abort.signal.aborted) setBusy(false); });
    } else if (localKey != null) {
      const j = saved.journeys.find(item => journeyKey(item) === localKey);
      if (j) { setResult(j); setOrigin(j.origin_id); setDestination(j.destination_id); setSpeed(j.speed_fraction_c); }
      else setError('Saved journey unavailable.');
    }
    return () => abort.abort();
  }, [sharedId, localKey, saved.journeys, attempt]);
  useEffect(() => {
    if (!playing) return;
    let last = performance.now();
    const timer = setInterval(() => { const now = performance.now(); const delta = (now - last) / 20000; last = now; setProgress(p => Math.min(1, p + delta)); }, 50);
    return () => clearInterval(timer);
  }, [playing]);
  useEffect(() => { if (progress >= 1) setPlaying(false); }, [progress]);
  function invalidate() { setResult(undefined); setError(''); setPlaying(false); setProgress(0); setShareUrl(''); }
  const body = (): JourneyInput => ({ snapshot_id: snapshotKey, origin_id: origin, destination_id: destination, speed_fraction_c: speed });
  async function calculate() {
    setBusy(true); setError(''); setPlaying(false); setProgress(0);
    try { setResult(await request<Estimate>('/api/journey/v1/estimate', post(body()))); }
    catch (e) { setResult(undefined); setError(message(e)); }
    finally { setBusy(false); }
  }
  async function share() {
    if (!result) return;
    setBusy(true); setError('');
    const input = { snapshot_id: result.snapshot_id, origin_id: result.origin_id, destination_id: result.destination_id, speed_fraction_c: result.speed_fraction_c };
    const serialized = JSON.stringify(input);
    if (pendingShare.current?.body !== serialized) pendingShare.current = { body: serialized, key: crypto.randomUUID() };
    try {
      const j = await request<SharedJourney>('/api/journey/v1/journeys', { ...post(input), headers: { 'Content-Type': 'application/json', 'Idempotency-Key': pendingShare.current!.key } });
      const url = new URL(`/journeys?snapshot=${j.snapshot_id}&id=${j.id}`, location.origin).href; setShareUrl(url); copy(url);
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  const actualSnapshot = result?.snapshot_id ?? snapshotKey;
  return <div className="journey-workspace"><aside className="panel planner"><p className="eyebrow">CONSTANT-SPEED SCENARIO</p><h1>Plan an interstellar journey</h1>
    <p>Straight lines. Extraordinary distances.</p>
    {frozen ? <><p>Frozen journey · {origin} → {destination}</p><a href={`/journeys?snapshot=${actualSnapshot}&origin=${origin}&destination=${destination}`}>Start a new calculation</a></> : <>
      <details open><summary>Origin: {origin === 'sun' ? 'Sun' : origin}</summary><Search title="Choose origin" snapshot={snapshotKey} includeSun onSelect={s => { setOrigin(s.source_id); invalidate(); }} /></details>
      <details><summary>Destination: {destination === 'sun' ? 'Sun' : destination}</summary><Search title="Choose destination" snapshot={snapshotKey} includeSun onSelect={s => { setDestination(s.source_id); invalidate(); }} /></details>
      <label>Speed (fraction of c)<input type="number" min={.001} max={.5} step={.001} value={speed} onChange={e => { setSpeed(e.target.valueAsNumber); invalidate(); }} /></label>
      <input aria-label="Cruise speed" type="range" min={.001} max={.5} step={.001} value={Number.isFinite(speed) ? speed : .1} onChange={e => { setSpeed(Number(e.target.value)); invalidate(); }} />
      <small>0.001c to 0.5c · default 0.1c</small><button className="primary" disabled={busy || origin === destination || !Number.isFinite(speed) || speed < .001 || speed > .5} onClick={calculate}>Calculate journey</button>
      {origin === destination && <p>Choose two different objects.</p>}</>}
    {busy && <p role="status">Working…</p>}{error && <p role="alert">{error}{frozen && <button onClick={() => setAttempt(a => a + 1)}>Retry journey</button>}</p>}
    {result && <><div className="result" data-testid="journey-result"><span>{number(result.distance_ly, 5)} ly · {number(result.distance_pc, 5)} pc</span><strong>{number(result.duration_julian_years, 4)} years</strong><small>Julian years at {result.speed_fraction_c}c · {number(result.speed_km_s)} km/s</small></div>
      <button onClick={() => save(result)}>Save journey</button><p>Creating a share stores an anonymous public record for 30 days. Anyone with its link can read it.</p>
      {shared ? <p>Expires {new Date(shared.expires_at).toLocaleString()}<br /><button onClick={() => copy(location.href)}>Copy shared link</button></p> : <button disabled={busy} onClick={share}>Create 30-day share</button>}
      {shareUrl && <a href={shareUrl}>Open shared journey</a>}<ul className="assumptions">{result.assumptions.map(a => <li key={a}>{a}</li>)}</ul></>}
    <p>No acceleration, gravity, relativity or spacecraft engineering. Positions are frozen at catalog epoch J2016.0.</p>
  </aside><section className="journey-map"><Atlas snapshot={actualSnapshot} view={{ ...view, observer: 'sun' }} route={result} progress={progress} cameraRef={cameraRef} onPick={() => {}} />
    <div className="playback"><p>Illustrative playback · 20 real seconds · {matchMedia('(prefers-reduced-motion: reduce)').matches ? 'Reduced motion: play only on request' : 'Play only on request'}</p>
      <button disabled={!result} onClick={() => { if (progress >= 1) setProgress(0); setPlaying(p => !p); }}>{playing ? 'Pause' : 'Play'}</button><button disabled={!result} onClick={() => { setPlaying(false); setProgress(0); }}>Restart</button>
      <label>Journey progress<input type="range" min={0} max={1} step={.001} value={progress} onChange={e => { setPlaying(false); setProgress(Number(e.target.value)); }} /></label><span>Year {number((result?.duration_julian_years ?? 0) * progress, 2)} / {number(result?.duration_julian_years, 2)}</span></div>
  </section></div>;
}

function SavedPage({ saved, store }: { saved: Saved; store: (items: Saved) => void }) {
  return <section className="document"><p className="eyebrow">YOUR LOCAL COLLECTION</p><h1>Saved discoveries</h1><p>Stored only in this browser. No account or sync. Limit: 100 stars and 50 journeys. Frozen journey summaries remain available after public links expire.</p>
    <h2>Stars ({saved.stars.length})</h2>{!saved.stars.length && <p>No saved stars yet. Explore the atlas to save one.</p>}
    {saved.stars.map(s => <article className="saved-row" key={`${s.snapshot_id}:${s.source_id}`}><a href={starLink(s)}>{label(s)}<small>{number(s.distance_ly, 4)} ly from Sun</small></a><button aria-label={`Remove ${label(s)}`} onClick={() => store({ ...saved, stars: saved.stars.filter(v => v !== s) })}>Remove</button></article>)}
    <h2>Journeys ({saved.journeys.length})</h2>{!saved.journeys.length && <p>No saved journeys yet.</p>}
    {saved.journeys.map((j, i) => <article className="saved-row" key={journeyKey(j)}><a href={`/journeys?snapshot=${j.snapshot_id}&local=${encodeURIComponent(journeyKey(j))}`}>{j.origin_id} → {j.destination_id}<small>{number(j.distance_ly, 4)} ly · {number(j.duration_julian_years, 4)} Julian years at {j.speed_fraction_c}c</small></a><button aria-label={`Remove journey ${i + 1}`} onClick={() => store({ ...saved, journeys: saved.journeys.filter(v => v !== j) })}>Remove</button></article>)}
    <button disabled={!saved.stars.length && !saved.journeys.length} onClick={() => { if (confirm('Clear all stars and journeys saved in this browser?')) store(EMPTY); }}>Clear all saved items</button>
  </section>;
}

function About({ snapshot }: { snapshot?: Snapshot }) {
  const [version, setVersion] = useState<Record<string, unknown>>();
  const [release, setRelease] = useState<Record<string, unknown>>();
  useEffect(() => { request<Record<string, unknown>>('/version.json').then(setVersion).catch(() => {}); request<Record<string, unknown>>('/release.json').then(setRelease).catch(() => {}); }, []);
  return <section className="document"><p className="eyebrow">THE DATA BEHIND THE DOTS</p><h1>A small window into our stellar neighborhood.</h1><p>Stellar Atlas is an educational DevOps project using the Gaia Catalogue of Nearby Stars (GCNS), derived from Gaia EDR3. The Sun is an application marker at the origin, not an invented Gaia row.</p>
    <h2>Measured, not live</h2><p>Positions are Galactic Cartesian coordinates at J2016.0. The catalog is probabilistic and incomplete; the map stops at 100 pc. Point sizes are enlarged. BP−RP styling is approximate and does not establish temperature, stellar radius, mass, planets or habitability. Observer views change geometry; they do not simulate apparent brightness, evolution or light-cone effects.</p>
    <h2>Data and attribution</h2><p>This work has made use of data from the European Space Agency (ESA) mission Gaia, processed by the Gaia Data Processing and Analysis Consortium (DPAC). Funding for DPAC has been provided by national institutions, in particular the institutions participating in the Gaia Multilateral Agreement.</p>
    <p><a href="https://www.cosmos.esa.int/web/gaia-users/license">Gaia data: CC BY-NC 3.0 IGO</a> · <a href="https://gea.esac.esa.int/archive/documentation/GEDR3/Miscellaneous/sec_credit_and_citation_instructions/">Gaia EDR3 credits and citations</a> · <a href="https://arxiv.org/abs/2012.02061">GCNS: Gaia Collaboration, Smart et al. (2021)</a></p>
    <p>Changes: selected fields, unit normalization, curated verified aliases, deterministic binary chunks and illustrative photometric styling. Original software is MIT licensed; that license does not relabel the dataset.</p>
    <dl><div><dt>Dataset</dt><dd>{snapshot?.snapshot_id ?? 'Unavailable'}</dd></div><div><dt>Raw SHA-256</dt><dd>{snapshot?.raw_sha256 ?? 'Unavailable'}</dd></div><div><dt>Epoch</dt><dd>J2016.0</dd></div><div><dt>Source commit</dt><dd>{String(version?.source_sha ?? 'Development build — not recorded')}</dd></div><div><dt>Application release</dt><dd>{String(release?.release_id ?? version?.release_id ?? 'Development build — not recorded')}</dd></div></dl>
    {snapshot && <p><a href={snapshot.source_url}>Catalog source</a>{snapshot.citation_urls.map(url => <span key={url}> · <a href={url}>Source citation</a></span>)}</p>}
    {release && <details><summary>Local release image metadata</summary><pre>{JSON.stringify(release, null, 2)}</pre></details>}
    <h2>Availability</h2><p>The app runs on existing local hardware. Access depends on its host, Docker and internet; future public access also requires Kubernetes and a temporary Cloudflare Quick Tunnel. There is no 24/7 uptime guarantee or permanent public hostname. This build is a local application.</p>
  </section>;
}
