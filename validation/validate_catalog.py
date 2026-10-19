import csv
import hashlib
import json
import math
import statistics
import struct
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIELDS = 'source_id,ra,dec,xcoord_50,ycoord_50,zcoord_50,dist_50,dist_16,dist_84,phot_g_mean_mag,phot_bp_mean_mag,phot_rp_mean_mag'
QUERY = 'SELECT ' + FIELDS + ' FROM gcns.main'
URL = 'https://dc.g-vo.org/tap/sync?' + urllib.parse.urlencode({'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'csv', 'MAXREC': '400000', 'QUERY': QUERY})
path = ROOT / 'gcns_required_fields.csv'
start = time.perf_counter()
request = urllib.request.Request(URL, headers={'User-Agent': 'StellarAtlas-course-feasibility/1.0'})
with urllib.request.urlopen(request, timeout=120) as response, path.open('wb') as output:
    status = response.status
    while chunk := response.read(1024 * 1024):
        output.write(chunk)
print(f'Downloaded {path.stat().st_size:,} bytes in {time.perf_counter() - start:.2f}s', flush=True)

def numeric(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None

ids, errors, nearest, radii = set(), [], [], []
counts = dict(rows=0, duplicate_ids=0, missing_xyz=0, missing_distance=0, valid_brightness=0, valid_color=0, valid_distance_interval=0, within_100pc=0, within_50ly=0, within_25ly=0, renderable=0)
with path.open(newline='', encoding='utf-8') as source, (ROOT / 'stars.bin').open('wb') as packed:
    reader = csv.DictReader(source)
    assert set(FIELDS.split(',')) <= set(reader.fieldnames), reader.fieldnames
    for row in reader:
        counts['rows'] += 1
        sid = row['source_id'].strip()
        counts['duplicate_ids'] += sid in ids
        ids.add(sid)
        xyz = [numeric(row[f'{axis}coord_50']) for axis in 'xyz']
        distance_kpc = numeric(row['dist_50'])
        g, bp, rp = (numeric(row[key]) for key in ['phot_g_mean_mag', 'phot_bp_mean_mag', 'phot_rp_mean_mag'])
        lo, hi = numeric(row['dist_16']), numeric(row['dist_84'])
        counts['valid_brightness'] += g is not None
        counts['valid_color'] += bp is not None and rp is not None
        counts['valid_distance_interval'] += all(v is not None for v in [lo, distance_kpc, hi]) and lo <= distance_kpc <= hi
        if any(v is None for v in xyz):
            counts['missing_xyz'] += 1
            continue
        radius = math.sqrt(sum(v*v for v in xyz))
        radii.append(radius)
        if distance_kpc is None:
            counts['missing_distance'] += 1
        else:
            errors.append(abs(radius - distance_kpc * 1000) / (distance_kpc * 1000))
        counts['within_100pc'] += radius <= 100
        counts['within_50ly'] += radius * 3.261563777 <= 50
        counts['within_25ly'] += radius * 3.261563777 <= 25
        t = max(0, min(1, ((bp-rp) if bp is not None and rp is not None else 1) / 4))
        rgb = (0.45 + 0.55*t, 0.68 - 0.25*t, 1 - 0.8*t)
        packed.write(struct.pack('<6f', *xyz, *rgb))
        counts['renderable'] += 1
        nearest.append({'source_id': sid, 'xyz_pc': xyz, 'distance_ly': radius*3.261563777, 'g_magnitude': g})

assert counts['rows'] == 331312, counts
assert counts['duplicate_ids'] == 0, counts
assert counts['missing_xyz'] == 0, counts
assert max(errors) < 1e-5, max(errors)
nearest.sort(key=lambda item: item['distance_ly'])
a, b = nearest[:2]
separation = math.dist(a['xyz_pc'], b['xyz_pc']) * 3.261563777
report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'source_url': URL, 'http_status': status, 'csv_bytes': path.stat().st_size, 'csv_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'counts': counts, 'coordinate_relative_error_max': max(errors), 'coordinate_relative_error_median': statistics.median(errors), 'radius_pc_min': min(radii), 'radius_pc_max': max(radii), 'packed_render_bytes': (ROOT/'stars.bin').stat().st_size, 'nearest_five': nearest[:5], 'calculation_example': {'from': a['source_id'], 'to': b['source_id'], 'separation_ly': separation, 'travel_years_at_0_1c': separation/0.1}, 'checks_passed': ['full_catalog_row_count', 'unique_source_ids', 'finite_xyz', 'xyz_norm_matches_distance_units']}
(ROOT/'catalog_validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
(ROOT/'nearest_stars.json').write_text(json.dumps(nearest[:100], indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
