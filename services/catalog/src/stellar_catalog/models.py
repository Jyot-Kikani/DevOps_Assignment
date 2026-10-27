from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime

ObjectID = Annotated[str, Field(strict=True, pattern=r"^(sun|[0-9]{1,20})$", examples=["5853498713190525696", "sun"])]
SnapshotID = Annotated[str, Field(strict=True, pattern=r"^[a-z0-9][a-z0-9-]{0,95}$", examples=["gcns-edr3-20261013-20271720"])]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Nonnegative = Annotated[Finite, Field(ge=0)]
Position = tuple[Finite, Finite, Finite]

class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class ErrorDetail(Model):
    location: list[str | int]
    reason: str

class Error(Model):
    code: str
    message: str
    request_id: Annotated[str, Field(max_length=64, pattern=r"^[A-Za-z0-9._-]+$")]
    details: list[ErrorDetail]

class ErrorResponse(Model):
    error: Error

class Health(Model):
    status: Literal["live", "ready", "unavailable"]

class Meta(Model):
    service: Literal["catalog", "search", "atlas_map", "snapshot", "calculation", "journey"]
    source_sha: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    release_id: Annotated[str, Field(pattern=r"^(r[0-9]+-a[0-9]+-[a-f0-9]{12}|local-[a-f0-9]{12})$")]
    schema_version: Literal[1]
    readiness: bool
    active_snapshot: SnapshotID | None

from pydantic import HttpUrl

class Counts(Model):
    total: Annotated[int, Field(ge=0)]
    within_100pc: Annotated[int, Field(ge=0)]
    within_50ly: Annotated[int, Field(ge=0)]
    within_25ly: Annotated[int, Field(ge=0)]

class Snapshot(Model):
    snapshot_id: SnapshotID
    epoch: Literal[2016.0]
    raw_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    source_url: HttpUrl
    citation_urls: list[HttpUrl]
    license_url: HttpUrl
    counts: Counts
    max_map_radius_pc: Literal[100]
    map_format_version: Literal[1]
    transform_version: Literal["1"]

class Star(Model):
    snapshot_id: SnapshotID
    source_id: ObjectID
    ordinal: Annotated[int, Field(ge=0, le=4294967295)]
    aliases: list[str]
    position_pc: Position
    distance_pc: Nonnegative
    distance_ly: Nonnegative
    distance_p16_pc: Nonnegative | None
    distance_p84_pc: Nonnegative | None
    ra_deg: Annotated[Finite, Field(ge=0, lt=360)] | None
    dec_deg: Annotated[Finite, Field(ge=-90, le=90)] | None
    g_magnitude: Finite | None
    bp_magnitude: Finite | None
    rp_magnitude: Finite | None
    color_index: Finite | None

class SearchResult(Model):
    snapshot_id: SnapshotID
    items: list[Star]
    next_cursor: Annotated[str, Field(max_length=512, pattern=r"^[A-Za-z0-9_-]+$")] | None

class Neighbor(Model):
    star: Star
    separation_ly: Nonnegative
    distance_from_sun_ly: Nonnegative

class Neighbors(Model):
    snapshot_id: SnapshotID
    origin_id: ObjectID
    radius_ly: Annotated[Finite, Field(gt=0, le=326.16)]
    items: list[Neighbor]

class PositionsRequest(Model):
    ids: Annotated[list[ObjectID], Field(min_length=1, max_length=2)]

class FrozenPosition(Model):
    source_id: ObjectID
    position_pc: Position

class Positions(Model):
    snapshot_id: SnapshotID
    items: Annotated[list[FrozenPosition], Field(min_length=1, max_length=2)]

class Chunk(Model):
    chunk_id: Annotated[str, Field(pattern=r"^[0-9]{6}$")]
    url: Annotated[str, Field(pattern=r"^/api/catalog/v1/snapshots/[a-z0-9-]+/chunks/[0-9]{6}\.bin$")]
    count: Annotated[int, Field(ge=1, le=8192)]
    first_ordinal: Annotated[int, Field(ge=1)]
    last_ordinal: Annotated[int, Field(ge=1)]
    min_radius_pc: Nonnegative
    max_radius_pc: Nonnegative
    uncompressed_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    compressed_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    uncompressed_bytes: Annotated[int, Field(ge=24)]
    compressed_bytes: Annotated[int, Field(gt=0)]

class MapManifest(Model):
    snapshot: Snapshot
    radius_ly: Annotated[Finite, Field(gt=0, le=326.16)]
    total_count: Annotated[int, Field(ge=0)]
    format_version: Literal[1]
    record_bytes: Literal[24]
    chunks: list[Chunk]
