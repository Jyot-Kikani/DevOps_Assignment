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
    service: Literal["catalog", "journey"]
    source_sha: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    release_id: Annotated[str, Field(pattern=r"^(r[0-9]+-a[0-9]+-[a-f0-9]{12}|local-[a-f0-9]{12})$")]
    schema_version: Literal[1]
    readiness: bool
    active_snapshot: SnapshotID | None

from uuid import UUID
from pydantic import model_validator

class EstimateRequest(Model):
    snapshot_id: SnapshotID
    origin_id: ObjectID
    destination_id: ObjectID
    speed_fraction_c: Annotated[Finite, Field(strict=True, ge=0.001, le=0.5, examples=[0.1])]

    @model_validator(mode="after")
    def distinct(self):
        if self.origin_id == self.destination_id:
            raise ValueError("Origin and destination must differ")
        return self

class Estimate(Model):
    snapshot_id: SnapshotID
    origin_id: ObjectID
    destination_id: ObjectID
    origin_position_pc: Position
    destination_position_pc: Position
    distance_pc: Nonnegative
    distance_ly: Nonnegative
    speed_fraction_c: Annotated[Finite, Field(ge=0.001, le=0.5)]
    speed_km_s: Nonnegative
    duration_julian_years: Nonnegative
    model_version: Literal["constant-speed-v1"]
    assumptions: list[str]

class Journey(Estimate):
    id: UUID
    created_at: AwareDatetime
    expires_at: AwareDatetime


class CatalogPosition(Model):
    source_id: ObjectID
    position_pc: Position


class CatalogPositions(Model):
    snapshot_id: SnapshotID
    items: Annotated[list[CatalogPosition],Field(min_length=2,max_length=2)]
