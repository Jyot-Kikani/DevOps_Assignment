"""Streaming CSV validation. This module performs no downloads or database writes."""
import csv
import hashlib
import math
from pathlib import Path
from stellar_common.ids import object_id
from stellar_common.units import PC_TO_LY

HEADER = ["source_id", "ra", "dec", "xcoord_50", "ycoord_50", "zcoord_50", "dist_50", "dist_16", "dist_84",
          "phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag"]
BASELINE_COUNTS = {"rows": 331312, "within_100pc": 300526, "within_50ly": 1151, "within_25ly": 142,
                   "valid_brightness": 330881, "valid_color": 324310, "valid_distance_interval": 331312}


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def number(value, optional=False):
    if optional and (value is None or value.strip() == ""):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("Nonfinite catalog measurement")
    return result


def rows(path):
    with Path(path).open(encoding="utf-8", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != HEADER:
            raise ValueError("CSV header differs from declared schema")
        for line, raw in enumerate(reader, start=2):
            try:
                if None in raw or any(v is None for v in raw.values()):
                    raise ValueError("CSV field count differs from header")
                source_id = object_id(raw["source_id"])
                if source_id == "sun":
                    raise ValueError("Sun is not a catalog row")
                xyz = tuple(number(raw[k]) for k in ("xcoord_50", "ycoord_50", "zcoord_50"))
                distance, low, high = (number(raw[k]) * 1000 for k in ("dist_50", "dist_16", "dist_84"))
                if not all(math.isfinite(x) and x > 0 for x in (distance, low, high)) or not low <= distance <= high:
                    raise ValueError("Positive ordered distance percentiles required")
                norm = math.hypot(*xyz)
                if not math.isclose(norm, distance, rel_tol=1e-5, abs_tol=0):
                    raise ValueError("Coordinate norm/kpc conversion mismatch")
                ra, dec = number(raw["ra"]), number(raw["dec"])
                if not 0 <= ra < 360 or not -90 <= dec <= 90:
                    raise ValueError("RA/declination outside bounds")
                g, bp, rp = (number(raw[k], optional=True) for k in ("phot_g_mean_mag", "phot_bp_mean_mag", "phot_rp_mean_mag"))
                yield {"source_id": source_id, "position_pc": xyz, "distance_pc": norm, "distance_ly": norm * PC_TO_LY,
                       "distance_p16_pc": low, "distance_p84_pc": high, "ra_deg": ra, "dec_deg": dec,
                       "g_magnitude": g, "bp_magnitude": bp, "rp_magnitude": rp,
                       "color_index": None if bp is None or rp is None else bp - rp,
                       "coordinate_relative_error": abs(norm - distance) / distance}
            except (TypeError, ValueError, OverflowError) as exc:
                raise ValueError(f"Catalog line {line}: {exc}") from None


def validate(path, *, expected_sha256=None, expected_counts=None, expected_rows=None, fixture=False):
    raw_sha = digest(path)
    if expected_sha256 is not None and raw_sha != expected_sha256:
        raise ValueError("Raw catalog checksum mismatch")
    counts = {k: 0 for k in BASELINE_COUNTS}
    ids = set()
    maximum = 0.0
    minimum_radius, maximum_radius = math.inf, 0.0
    nearest = []
    for row in rows(path):
        source_id = row["source_id"]
        if source_id in ids:
            raise ValueError("Duplicate catalog source ID")
        ids.add(source_id)
        counts["rows"] += 1
        counts["within_100pc"] += row["distance_pc"] <= 100
        counts["within_50ly"] += row["distance_ly"] <= 50
        counts["within_25ly"] += row["distance_ly"] <= 25
        counts["valid_brightness"] += row["g_magnitude"] is not None
        counts["valid_color"] += row["color_index"] is not None
        counts["valid_distance_interval"] += 1
        maximum = max(maximum, row["coordinate_relative_error"])
        minimum_radius = min(minimum_radius, row["distance_pc"])
        maximum_radius = max(maximum_radius, row["distance_pc"])
        if len(nearest) < 5 or row["distance_pc"] < nearest[-1]["distance_pc"]:
            nearest.append({k: row[k] for k in ("source_id", "position_pc", "distance_pc", "distance_ly")})
            nearest.sort(key=lambda r: (r["distance_pc"], int(r["source_id"])))
            nearest = nearest[:5]
    if not counts["rows"]:
        raise ValueError("Empty catalog")
    if expected_counts is not None and any(counts.get(k) != v for k, v in expected_counts.items()):
        raise ValueError("Catalog counts differ from declared manifest")
    if expected_rows is not None and counts["rows"] != expected_rows:
        raise ValueError("Catalog row count differs from declared fixture manifest")
    return {"status": "passed", "fixture": fixture, "raw_sha256": raw_sha, "raw_bytes": Path(path).stat().st_size,
            "header": HEADER, "counts": counts, "unique_ids": len(ids), "coordinate_relative_error_max": maximum,
            "radius_pc_min": minimum_radius, "radius_pc_max": maximum_radius, "nearest_five": nearest,
            "optional_photometry": "Missing G/BP/RP normalized to null; no missing row rejected or replaced with zero"}
