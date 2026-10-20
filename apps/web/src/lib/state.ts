import type { Estimate, Star } from './api';
import type { Position } from './map-format';

export const RADII = [25, 50, 100, 200, 326.16];
export const PC_LY = 3.261563777;
export const radiusPc = (radius: number) => radius === 326.16 ? 100 : radius / PC_LY;
export const objectId = (id: string | null): string => id && /^(sun|[0-9]{1,20})$/.test(id) ? id : 'sun';
export const snapshotId = (id: string | null) => id && /^[a-z0-9][a-z0-9-]{0,95}$/.test(id) ? id : null;
const vector = (text: string | null): Position | undefined => {
  if (!text) return;
  const values = text.split(',').map(Number);
  if (values.length === 3 && values.every(v => Number.isFinite(v) && Math.abs(v) <= 2000)) return values as unknown as Position;
};
export type View = ReturnType<typeof readView>;
export function readView(params = new URLSearchParams(location.search)) {
  const radius = Number(params.get('radius'));
  return { snapshot: snapshotId(params.get('snapshot')), selected: objectId(params.get('star')),
    radius: RADII.includes(radius) ? radius : 50, labels: params.get('labels') !== '0',
    plane: params.get('plane') !== '0', rings: params.get('rings') !== '0',
    observer: objectId(params.get('observer')), camera: vector(params.get('camera')), target: vector(params.get('target')) };
}
export function viewUrl(view: View, camera?: { camera: Position; target: Position }) {
  const url = new URL('/explore', location.origin);
  for (const [key, value] of Object.entries(view)) {
    if (value != null) url.searchParams.set(key === 'selected' ? 'star' : key,
      Array.isArray(value) ? value.join(',') : typeof value === 'boolean' ? (value ? '1' : '0') : String(value));
  }
  if (camera) for (const [key, value] of Object.entries(camera)) url.searchParams.set(key, value.join(','));
  return url;
}
export type Saved = { stars: Star[]; journeys: Estimate[] };
export const EMPTY: Saved = { stars: [], journeys: [] };
const finitePosition = (p: unknown) => Array.isArray(p) && p.length === 3 && p.every(v => typeof v === 'number' && Number.isFinite(v));
export function validEstimate(value: unknown): value is Estimate {
  if (!value || typeof value !== 'object') return false;
  const e = value as Estimate;
  return !!snapshotId(e.snapshot_id) && objectId(e.origin_id) === e.origin_id && objectId(e.destination_id) === e.destination_id &&
    e.origin_id !== e.destination_id && e.model_version === 'constant-speed-v1' && finitePosition(e.origin_position_pc) && finitePosition(e.destination_position_pc) &&
    [e.distance_pc, e.distance_ly, e.speed_fraction_c, e.speed_km_s, e.duration_julian_years].every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0) &&
    e.speed_fraction_c >= .001 && e.speed_fraction_c <= .5 && Array.isArray(e.assumptions) && e.assumptions.every(a => typeof a === 'string');
}
export function readSaved(storage: Pick<Storage, 'getItem'>): Saved {
  const value = JSON.parse(storage.getItem('stellar-atlas-v1') ?? '{"stars":[],"journeys":[]}');
  return { stars: Array.isArray(value?.stars) ? value.stars.filter((s: Star) => s && snapshotId(s.snapshot_id) && objectId(s.source_id) === s.source_id &&
    Array.isArray(s.aliases) && s.aliases.every(a => typeof a === 'string') && finitePosition(s.position_pc) && Number.isFinite(s.distance_ly)).slice(0, 100) : [],
    journeys: Array.isArray(value?.journeys) ? value.journeys.filter(validEstimate).slice(0, 50) : [] };
}
export const journeyKey = (e: Estimate) => `${e.snapshot_id}:${e.origin_id}:${e.destination_id}:${e.speed_fraction_c}`;
export function addSaved(saved: Saved, item: Star | Estimate): Saved {
  if ('source_id' in item) {
    const stars = saved.stars.filter(s => s.source_id !== item.source_id || s.snapshot_id !== item.snapshot_id);
    if (stars.length >= 100) throw new Error('The limit is 100 saved stars. Remove one first.');
    return { ...saved, stars: [...stars, item] };
  }
  const journeys = saved.journeys.filter(j => journeyKey(j) !== journeyKey(item));
  if (journeys.length >= 50) throw new Error('The limit is 50 saved journeys. Remove one first.');
  return { ...saved, journeys: [...journeys, item] };
}
