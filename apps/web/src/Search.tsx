import { useEffect, useRef, useState } from 'react';
import { catalog, label, number, request } from './lib/api';
import type { SearchResult, Star } from './lib/api';

export function Search({ snapshot, radius, onSelect, title = 'Search stars', includeSun = false }: {
  snapshot: string; radius?: number; onSelect: (star: Star) => void; title?: string; includeSun?: boolean;
}) {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<Star[]>([]);
  const [status, setStatus] = useState('Loading stars…');
  const [attempt, setAttempt] = useState(0);
  const resultRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    setStatus('Loading stars…');
    const timer = setTimeout(async () => {
      try {
        const params = new URLSearchParams({ q: query, limit: '20' });
        if (radius) params.set('radius_ly', String(radius));
        const result = await request<SearchResult>(`${catalog(snapshot)}/stars?${params}`, { signal: controller.signal });
        const sun = includeSun && (!query || 'sun'.startsWith(query.toLowerCase())) ?
          await request<Star>(`${catalog(snapshot)}/stars/sun`, { signal: controller.signal }) : null;
        setItems((sun ? [sun, ...result.items] : result.items).slice(0, 20));
        setStatus('');
      } catch (error) { if (!controller.signal.aborted) { setItems([]); setStatus(error instanceof Error ? error.message : 'Search failed.'); } }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [snapshot, radius, query, includeSun, attempt]);
  return <section className="search"><label>{title}<input type="search" value={query} maxLength={100} placeholder="Name or Gaia source ID" onChange={e => setQuery(e.target.value)}
    onKeyDown={e => { if (e.key === 'ArrowDown') { e.preventDefault(); resultRef.current?.querySelector<HTMLButtonElement>('button')?.focus(); } }} /></label>
    <div role="status">{status}</div>{status && status !== 'Loading stars…' && <button onClick={() => setAttempt(v => v + 1)}>Retry search</button>}
    {!status && !items.length && <p>No matching stars.</p>}
    <div className="star-list" ref={resultRef} onKeyDown={e => {
      if (!['ArrowDown', 'ArrowUp'].includes(e.key)) return;
      const buttons = Array.from(resultRef.current?.querySelectorAll('button') ?? []);
      const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
      e.preventDefault(); buttons[(index + (e.key === 'ArrowDown' ? 1 : -1) + buttons.length) % buttons.length]?.focus();
    }}>{items.map(star => <button key={star.source_id} onClick={() => onSelect(star)}><span>{label(star)}</span><small>{number(star.distance_ly)} ly from Sun</small></button>)}</div>
  </section>;
}
