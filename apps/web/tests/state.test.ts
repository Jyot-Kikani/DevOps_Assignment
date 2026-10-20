import { describe, expect, it } from 'vitest';
import { addSaved, EMPTY, radiusPc, readSaved, readView, validEstimate } from '../src/lib/state';
import type { Estimate } from '../src/lib/api';

const journey: Estimate = { snapshot_id: 'fixture-test', origin_id: 'sun', destination_id: '5853498713190525696',
  origin_position_pc: [0, 0, 0], destination_position_pc: [3, 4, 0], distance_pc: 5, distance_ly: 16.307818885,
  speed_fraction_c: .1, speed_km_s: 29979.2458, duration_julian_years: 163.07818885,
  model_version: 'constant-speed-v1', assumptions: ['No acceleration, gravity or relativity'] };

describe('public view and local saves', () => {
  it('validates untrusted links and keeps the 100 pc preset exact', () => {
    const view = readView(new URLSearchParams('radius=NaN&star=<script>&camera=Infinity,0,1&snapshot=../../&observer=oops&plane=0'));
    expect(view.radius).toBe(50); expect(view.selected).toBe('sun'); expect(view.camera).toBeUndefined();
    expect(view.snapshot).toBeNull(); expect(view.observer).toBe('sun'); expect(view.plane).toBe(false);
    expect(radiusPc(326.16)).toBe(100);
    expect(readView(new URLSearchParams('star=5853498713190525696')).selected).toBe('5853498713190525696');
  });
  it('deduplicates frozen local journeys and enforces the limit', () => {
    const saved = addSaved(addSaved(EMPTY, journey), journey);
    expect(saved.journeys).toHaveLength(1);
    expect(readSaved({ getItem: () => JSON.stringify(saved) })).toEqual(saved);
    const full = { stars: [], journeys: Array.from({ length: 50 }, (_, i) => ({ ...journey, destination_id: String(i + 1) })) };
    expect(() => addSaved(full, journey)).toThrow('50 saved journeys');
    expect(validEstimate({ ...journey, speed_fraction_c: Infinity })).toBe(false);
    expect(readSaved({ getItem: () => '{"stars":[{}],"journeys":[{}]}' })).toEqual(EMPTY);
  });
});
