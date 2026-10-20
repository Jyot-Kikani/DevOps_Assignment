"""Frozen v1 SQLAlchemy schema. Future revisions add their own definitions."""
from sqlalchemy import (MetaData, Table, Column, Text, Integer, Float, Boolean, DateTime,
                        CheckConstraint, ForeignKey, ForeignKeyConstraint, UniqueConstraint, LargeBinary, text)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData(schema="catalog")
snapshots = Table("snapshots", metadata,
    Column("id", Text, primary_key=True), Column("raw_sha256", Text, nullable=False),
    Column("transform_version", Text, nullable=False), Column("schema_version", Integer, nullable=False),
    Column("epoch", Float, nullable=False), Column("source_url", Text, nullable=False),
    Column("provenance", JSONB, nullable=False), Column("total_rows", Integer, nullable=False),
    Column("in_scope_rows", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("status", Text, nullable=False),
    CheckConstraint("status IN ('staging','ready','failed')"),
    CheckConstraint("id ~ '^[a-z0-9][a-z0-9-]{0,95}$' AND raw_sha256 ~ '^[a-f0-9]{64}$'"),
    CheckConstraint("total_rows > 0 AND in_scope_rows >= 0 AND in_scope_rows <= total_rows"),
    CheckConstraint("schema_version = 1 AND epoch = 2016.0 AND transform_version = '1'"))
stars = Table("stars", metadata,
    Column("snapshot_id", Text, ForeignKey("catalog.snapshots.id"), primary_key=True),
    Column("source_id", Text, primary_key=True), Column("ordinal", Integer, nullable=False),
    *[Column(k, Float, nullable=False) for k in ("x", "y", "z", "distance_pc", "distance_ly", "distance_p16_pc", "distance_p84_pc", "ra_deg", "dec_deg")],
    *[Column(k, Float) for k in ("g_magnitude", "bp_magnitude", "rp_magnitude", "color_index")],
    UniqueConstraint("snapshot_id", "ordinal"),
    CheckConstraint("source_id ~ '^[0-9]{1,20}$' AND ordinal > 0"),
    CheckConstraint("distance_p16_pc > 0 AND distance_p16_pc <= distance_pc * 1.00001 AND distance_pc <= distance_p84_pc * 1.00001"),
    CheckConstraint("distance_pc > 0 AND distance_ly > 0 AND ra_deg >= 0 AND ra_deg < 360 AND dec_deg BETWEEN -90 AND 90"),
    *[CheckConstraint(f"{k} > '-Infinity'::float8 AND {k} < 'Infinity'::float8") for k in
      ("x", "y", "z", "distance_pc", "distance_ly", "distance_p16_pc", "distance_p84_pc", "ra_deg", "dec_deg", "g_magnitude", "bp_magnitude", "rp_magnitude", "color_index")])
aliases = Table("aliases", metadata,
    Column("snapshot_id", Text, primary_key=True), Column("source_id", Text, primary_key=True),
    Column("alias", Text, nullable=False), Column("normalized_alias", Text, primary_key=True),
    ForeignKeyConstraint(["snapshot_id", "source_id"], ["catalog.stars.snapshot_id", "catalog.stars.source_id"]))
chunks = Table("map_chunks", metadata,
    Column("snapshot_id", Text, ForeignKey("catalog.snapshots.id"), primary_key=True),
    Column("chunk_id", Text, primary_key=True),
    *[Column(k, Integer, nullable=False) for k in ("count", "first_ordinal", "last_ordinal", "format_version", "uncompressed_bytes", "compressed_bytes")],
    Column("min_radius_pc", Float, nullable=False), Column("max_radius_pc", Float, nullable=False),
    Column("gzip", LargeBinary, nullable=False), Column("uncompressed_sha256", Text, nullable=False),
    Column("compressed_sha256", Text, nullable=False),
    CheckConstraint("chunk_id ~ '^[0-9]{6}$' AND count BETWEEN 1 AND 8192 AND format_version = 1"),
    CheckConstraint("first_ordinal > 0 AND last_ordinal = first_ordinal + count - 1 AND uncompressed_bytes = count * 24"),
    CheckConstraint("min_radius_pc > 0 AND min_radius_pc <= max_radius_pc AND max_radius_pc <= 100"),
    CheckConstraint("compressed_bytes = octet_length(gzip) AND compressed_bytes > 0"),
    CheckConstraint("uncompressed_sha256 ~ '^[a-f0-9]{64}$' AND compressed_sha256 ~ '^[a-f0-9]{64}$'"))
active = Table("active_snapshot", metadata,
    Column("singleton", Boolean, primary_key=True), Column("snapshot_id", Text, ForeignKey("catalog.snapshots.id"), nullable=False),
    CheckConstraint("singleton = true"))
