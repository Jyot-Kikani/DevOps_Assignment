"""Frozen v1 Journey schema; no Catalog imports or cross-database connection."""
from sqlalchemy import MetaData, Table, Column, Text, Float, DateTime, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

metadata = MetaData(schema="journey")
journeys = Table("journeys", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("idempotency_key", UUID(as_uuid=True), unique=True, nullable=False),
    *[Column(k, Text, nullable=False) for k in ("request_hash", "snapshot_id", "origin_id", "destination_id", "model_version")],
    Column("origin_position_pc", ARRAY(Float), nullable=False), Column("destination_position_pc", ARRAY(Float), nullable=False),
    *[Column(k, Float, nullable=False) for k in ("distance_pc", "distance_ly", "speed_fraction_c", "speed_km_s", "duration_julian_years")],
    Column("assumptions", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    CheckConstraint("origin_id ~ '^(sun|[0-9]{1,20})$' AND destination_id ~ '^(sun|[0-9]{1,20})$' AND origin_id <> destination_id"),
    CheckConstraint("request_hash ~ '^[a-f0-9]{64}$' AND snapshot_id ~ '^[a-z0-9][a-z0-9-]{0,95}$'"),
    CheckConstraint("speed_fraction_c BETWEEN 0.001 AND 0.5 AND model_version = 'constant-speed-v1'"),
    CheckConstraint("expires_at = created_at + interval '30 days'"),
    *[CheckConstraint(f"array_length({k}, 1) = 3 AND array_ndims({k}) = 1 AND array_position({k},NULL) IS NULL AND '-Infinity'::float8 < ALL({k}) AND 'Infinity'::float8 > ALL({k})")
      for k in ("origin_position_pc", "destination_position_pc")],
    *[CheckConstraint(f"{k} >= 0 AND {k} < 'Infinity'::float8") for k in ("distance_pc", "distance_ly", "speed_km_s", "duration_julian_years")])
