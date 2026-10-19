import { describe, expect, it } from "vitest";
import { decodeMap, scenePosition } from "../src/lib/map-format";
import type { components } from "../src/generated/catalog";

const golden = "010000000000803f0000004000004040000080400000a0400200000000000000000080bf0000003f0000c07f0000c07f";

describe("map wire contract", () => {
  it("decodes independent little-endian golden bytes and nullable photometry", () => {
    const bytes = Uint8Array.from(golden.match(/../g)!.map(s => parseInt(s, 16)));
    expect(decodeMap(bytes.buffer)).toEqual([
      { ordinal: 1, positionPc: [1, 2, 3], gMagnitude: 4, colorIndex: 5 },
      { ordinal: 2, positionPc: [0, -1, 0.5], gMagnitude: null, colorIndex: null },
    ]);
    expect(() => decodeMap(new ArrayBuffer(23))).toThrow("Truncated");
  });
  it("rotates the basis with positive handedness", () => {
    expect(scenePosition([1, 0, 0])).toEqual([1, 0, -0]);
    expect(scenePosition([0, 1, 0])).toEqual([0, 0, -1]);
    expect(scenePosition([0, 0, 1])).toEqual([0, 1, -0]);
    const [a, b, c] = scenePosition([1, 0, 0]);
    const [d, e, f] = scenePosition([0, 1, 0]);
    const cross = [b * f - c * e, c * d - a * f, a * e - b * d];
    expect(cross.map(v => v || 0)).toEqual(scenePosition([0, 0, 1]).map(v => v || 0));
    expect(() => scenePosition([Infinity, 0, 0])).toThrow();
  });
  it("preserves a Gaia ID beyond JavaScript integer precision", () => {
    const id: components["schemas"]["Star"]["source_id"] = "5853498713190525696";
    expect(JSON.parse(JSON.stringify({ id })).id).toBe("5853498713190525696");
    // @ts-expect-error generated transport IDs must never accept numbers
    const invalid: components["schemas"]["Star"]["source_id"] = 5853498713190525696;
    expect(typeof invalid).toBe("number");
  });
});
