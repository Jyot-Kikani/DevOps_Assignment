export const RECORD_BYTES = 24;
export type Position = readonly [number, number, number];
export type MapRecord = Readonly<{
  ordinal: number; positionPc: Position; gMagnitude: number | null; colorIndex: number | null;
}>;

export function scenePosition([x, y, z]: Position): Position {
  if (![x, y, z].every(Number.isFinite)) throw new Error("Nonfinite position");
  return [x, z, -y];
}

export function decodeMap(buffer: ArrayBuffer): readonly MapRecord[] {
  if (buffer.byteLength % RECORD_BYTES !== 0) throw new Error("Truncated map record");
  const view = new DataView(buffer);
  const records: MapRecord[] = [];
  for (let offset = 0; offset < buffer.byteLength; offset += RECORD_BYTES) {
    const ordinal = view.getUint32(offset, true);
    const positionPc: Position = [4, 8, 12].map(n => view.getFloat32(offset + n, true)) as unknown as Position;
    const g = view.getFloat32(offset + 16, true);
    const color = view.getFloat32(offset + 20, true);
    if (!ordinal || !positionPc.every(Number.isFinite) || [g, color].some(v => !Number.isFinite(v) && !Number.isNaN(v))) {
      throw new Error("Invalid map record");
    }
    records.push({ ordinal, positionPc, gMagnitude: Number.isNaN(g) ? null : g, colorIndex: Number.isNaN(color) ? null : color });
  }
  return records;
}
