"""Offline, transactional catalog import. No remote source fetch or HTTP endpoint."""
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
from sqlalchemy import text
from stellar_common.database import engine_for
from stellar_common.ids import snapshot_id
from stellar_common.map_format import MapRecord, encode, deterministic_gzip, CHUNK_RECORDS
from .validation import HEADER, digest, rows, validate

FIELDS = ("source_id", "x", "y", "z", "distance_pc", "distance_ly", "distance_p16_pc", "distance_p84_pc",
          "ra_deg", "dec_deg", "g_magnitude", "bp_magnitude", "rp_magnitude", "color_index")


def preflight(path, manifest_path, archive=None, aliases_path=None):
    manifest = json.loads(Path(manifest_path).read_text())
    snapshot_id(manifest["snapshot_id"])
    if manifest["catalog_schema_version"] != 1 or manifest["transform_version"] != "1" or manifest["epoch"] != 2016.0 or manifest["header"] != HEADER:
        raise ValueError("Unsupported catalog schema, epoch or transformation")
    if type(manifest.get("fixture")) is not bool or (manifest["fixture"] and os.environ.get("APP_ENV") == "demo"):
        raise ValueError("Demo imports must use real sealed catalogs")
    if not manifest["fixture"]:
        if archive is None or digest(archive) != manifest["archive_sha256"] or Path(archive).stat().st_size != manifest["archive_bytes"]:
            raise ValueError("Archive checksum/size mismatch")
        with gzip.open(archive, "rb") as source:
            raw_hash = hashlib.file_digest(source, "sha256").hexdigest()
        if raw_hash != manifest["raw_sha256"]:
            raise ValueError("Archive does not contain the declared raw bytes")
    checked = validate(path, expected_sha256=manifest["raw_sha256"], expected_counts=manifest["counts"], fixture=manifest["fixture"])
    if checked["raw_bytes"] != manifest["raw_bytes"]:
        raise ValueError("Raw catalog size mismatch")
    aliases = []
    if aliases_path:
        if digest(aliases_path) != manifest["notices"]["aliases.csv"]["sha256"]:
            raise ValueError("Curated alias checksum mismatch")
        with Path(aliases_path).open(newline="", encoding="utf-8") as source:
            for row in csv.DictReader(source):
                aliases.append((row["source_id"], row["alias"], row["alias"].casefold()))
    return manifest, checked, aliases


def normalized(path):
    # Compact tuples keep the full frozen catalog within the 512 MiB import budget.
    output = []
    for row in rows(path):
        output.append((row["source_id"], *row["position_pc"], *[row[k] for k in FIELDS[4:]]))
    output.sort(key=lambda r: (r[4], int(r[0])))
    return output


def make_chunks(records):
    # Only map-scope objects are transferred; profiles still retain every catalog row.
    block = []
    for ordinal, row in enumerate(records, 1):
        if row[4] > 100:
            break
        block.append((ordinal, row))
        if len(block) == CHUNK_RECORDS:
            yield chunk_record(block)
            block = []
    if block:
        yield chunk_record(block)


def chunk_record(block):
    raw = encode(MapRecord(ordinal, row[1], row[2], row[3], row[10], row[13]) for ordinal, row in block)
    zipped = deterministic_gzip(raw)
    first, last = block[0][0], block[-1][0]
    return {"chunk_id": f"{(first - 1) // CHUNK_RECORDS:06d}", "count": len(block), "first_ordinal": first,
            "last_ordinal": last, "min_radius_pc": block[0][1][4], "max_radius_pc": block[-1][1][4],
            "format_version": 1, "uncompressed_bytes": len(raw), "compressed_bytes": len(zipped),
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(), "compressed_sha256": hashlib.sha256(zipped).hexdigest(), "gzip": zipped}


def load_catalog(path, manifest_path, *, archive=None, aliases_path=None, activate=False, after_staging=None):
    started = time.perf_counter()
    manifest, checked, aliases = preflight(path, manifest_path, archive, aliases_path)
    records = normalized(path)
    if digest(path) != manifest["raw_sha256"]:
        raise ValueError("Catalog changed during normalization")
    sid = manifest["snapshot_id"]
    engine = engine_for("CATALOG_WRITER_DSN", "catalog_writer", "stellar_catalog")
    reused, activated = False, False
    try:
        with engine.begin() as connection:
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtext('stellar-catalog-import'))"))
            existing = connection.execute(text("SELECT * FROM catalog.snapshots WHERE id=:s"), {"s": sid}).mappings().first()
            if existing:
                if existing["status"] != "ready" or existing["provenance"] != manifest:
                    raise ValueError("Existing snapshot identity/provenance conflict")
                reused = True
            else:
                connection.execute(text("""INSERT INTO catalog.snapshots
                    (id,raw_sha256,transform_version,schema_version,epoch,source_url,provenance,total_rows,in_scope_rows,status)
                    VALUES (:s,:sha,'1',1,2016.0,:url,CAST(:p AS jsonb),:total,:scope,'staging')"""),
                    {"s": sid, "sha": manifest["raw_sha256"], "url": manifest["source_url"], "p": json.dumps(manifest),
                     "total": checked["counts"]["rows"], "scope": checked["counts"]["within_100pc"]})
                sql = "COPY catalog.stars (snapshot_id,ordinal," + ",".join(FIELDS) + ") FROM STDIN"
                with connection.connection.driver_connection.cursor() as cursor:
                    with cursor.copy(sql) as copy:
                        for ordinal, row in enumerate(records, 1):
                            copy.write_row((sid, ordinal, *row))
                for source_id, alias, normalized_alias in aliases:
                    connection.execute(text("INSERT INTO catalog.aliases VALUES (:s,:id,:a,:n)"),
                                       {"s": sid, "id": source_id, "a": alias, "n": normalized_alias})
                if after_staging:
                    after_staging(connection)  # Test seam; never exposed as a public CLI option.
            # Verify persisted rows/ordinals/content even on same-snapshot retries.
            cursor = connection.connection.driver_connection.cursor(name="verify_stars")
            cursor.itersize = 8192
            cursor.execute("SELECT ordinal," + ",".join(FIELDS) + " FROM catalog.stars WHERE snapshot_id=%s ORDER BY ordinal", (sid,))
            for (ordinal, row), stored in zip(enumerate(records, 1), cursor, strict=True):
                if tuple(stored) != (ordinal, *row):
                    raise ValueError("Persisted catalog row verification failed")
            cursor.close()
            stored_aliases = connection.execute(text("SELECT source_id,alias,normalized_alias FROM catalog.aliases WHERE snapshot_id=:s ORDER BY source_id,normalized_alias"), {"s": sid}).all()
            if sorted(tuple(r) for r in stored_aliases) != sorted(aliases):
                raise ValueError("Persisted alias verification failed")
            total_chunks, compressed, default_compressed = 0, 0, 0
            for chunk in make_chunks(records):
                chunk["snapshot_id"] = sid
                if not reused:
                    keys = list(chunk)
                    connection.execute(text("INSERT INTO catalog.map_chunks (" + ",".join(keys) + ") VALUES (" + ",".join(":" + k for k in keys) + ")"), chunk)
                else:
                    stored = connection.execute(text("SELECT * FROM catalog.map_chunks WHERE snapshot_id=:s AND chunk_id=:c"), {"s": sid, "c": chunk["chunk_id"]}).mappings().first()
                    if stored is None or dict(stored) != chunk:
                        raise ValueError("Persisted map chunk verification failed")
                total_chunks += 1
                compressed += chunk["compressed_bytes"]
                if chunk["min_radius_pc"] * 3.261563777 <= 50:
                    default_compressed += chunk["compressed_bytes"]
            actual = connection.execute(text("SELECT count(*), COALESCE(sum(count),0) FROM catalog.map_chunks WHERE snapshot_id=:s"), {"s": sid}).one()
            if actual != (total_chunks, checked["counts"]["within_100pc"]):
                raise ValueError("Persisted map counts mismatch")
            if not reused:
                connection.execute(text("UPDATE catalog.snapshots SET status='ready' WHERE id=:s"), {"s": sid})
            if activate:
                current = connection.execute(text("SELECT snapshot_id FROM catalog.active_snapshot WHERE singleton=true")).scalar()
                activated = current != sid
                if activated:
                    connection.execute(text("INSERT INTO catalog.active_snapshot VALUES (true,:s) ON CONFLICT(singleton) DO UPDATE SET snapshot_id=excluded.snapshot_id"), {"s": sid})
        return {"status": "passed", "snapshot_id": sid, "reused": reused, "activated": activated,
                "counts": checked["counts"], "chunks": total_chunks, "map_compressed_bytes": compressed,
                "default_50ly_chunk_bytes": default_compressed, "duration_seconds": round(time.perf_counter() - started, 3)}
    finally:
        engine.dispose()


def report():
    engine = engine_for("CATALOG_WRITER_DSN", "catalog_writer", "stellar_catalog")
    try:
        with engine.connect() as c:
            snapshots = c.execute(text("SELECT id,status,total_rows,in_scope_rows FROM catalog.snapshots ORDER BY id")).mappings().all()
            active = c.execute(text("SELECT snapshot_id FROM catalog.active_snapshot WHERE singleton=true")).scalar()
        return {"status": "passed", "active_snapshot": active, "snapshots": [dict(r) for r in snapshots]}
    finally:
        engine.dispose()
