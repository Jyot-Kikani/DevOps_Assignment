import type { components as Catalog } from '../generated/catalog';
import type { components as Journey } from '../generated/journey';

export type Star = Catalog['schemas']['Star'];
export type Snapshot = Catalog['schemas']['Snapshot'];
export type Manifest = Catalog['schemas']['MapManifest'];
export type SearchResult = Catalog['schemas']['SearchResult'];
export type Neighbors = Catalog['schemas']['Neighbors'];
export type Estimate = Journey['schemas']['Estimate'];
export type SharedJourney = Journey['schemas']['Journey'];
export type JourneyInput = Journey['schemas']['EstimateRequest'];
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, signal: init?.signal ?? AbortSignal.timeout(15000) });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new ApiError(response.status, response.status === 410 ? 'This shared journey has expired.' :
      response.status === 404 ? 'This item is unavailable.' : body?.error?.message ?? 'Service unavailable. Please retry.');
  }
  return response.json();
}
export const catalog = (snapshot: string) => `/api/catalog/v1/snapshots/${encodeURIComponent(snapshot)}`;
export const label = (star: Star) => star.source_id === 'sun' ? 'Sun' : star.aliases[0] ?? star.source_id;
export const number = (value: number | null | undefined, digits = 3) => value == null ? 'Not available' : value.toLocaleString(undefined, { maximumFractionDigits: digits });
export const post = (body: unknown): RequestInit => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
