"""Machine-checkable deployment and phase evidence contracts. No runtime credentials."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime, model_validator

SHA = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Commit = Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
Phase = Annotated[str, Field(pattern=r"^P(0[0-9]|1[0-9]|2[0-3])$")]
Status = Literal["not_run", "in_progress", "passed", "failed", "blocked"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Dataset(Model):
    snapshot_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,95}$")]
    raw_sha256: SHA
    fixture: Literal[False]


class Image(Model):
    # Local Docker IDs are usable immutable references; registry refs belong to P15.
    ref: Annotated[str, Field(pattern=r"^(sha256:[a-f0-9]{64}|ghcr\.io/[a-z0-9-]+/stellar-atlas-(web|catalog|search|atlas-map|snapshot|calculation|journey|importer)@sha256:[a-f0-9]{64})$")]
    manifest_digest: Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]
    local_tag: str | None = None


class Images(Model):
    web: Image
    catalog: Image
    journey: Image
    importer: Image
    search: Image | None = None
    atlas_map: Image | None = Field(default=None, alias="atlas-map")
    snapshot: Image | None = None
    calculation: Image | None = None


class Compatibility(Model):
    catalog_schema: Literal[1]
    journey_schema: Literal[1]
    model: Literal["constant-speed-v1"]


class Release(Model):
    schema_version: Literal[1]
    release_id: Annotated[str, Field(pattern=r"^(r[0-9]+-a[0-9]+-[a-f0-9]{12}|local-[a-f0-9]{12})$")]
    source_sha: Commit
    source_repository: Annotated[str, Field(pattern=r"^[A-Za-z0-9-]+/DevOps_Assignment$")]
    created_at: AwareDatetime
    dataset: Dataset
    images: Images
    source_dirty: Literal[False] = False
    compatibility: Compatibility

    @model_validator(mode="after")
    def consistency(self):
        if self.created_at.utcoffset().total_seconds() != 0:
            raise ValueError("Release timestamp must use UTC")
        if not self.release_id.endswith(self.source_sha[:12]):
            raise ValueError("Release suffix must match source SHA")
        owner = self.source_repository.split("/")[0].lower()
        extracted = [self.images.search, self.images.atlas_map, self.images.snapshot, self.images.calculation]
        if any(image is not None for image in extracted) and not all(image is not None for image in extracted):
            raise ValueError("Six-service release must include all four extracted service images")
        for role, image in self.images:
            if image is None:
                continue
            role = role.replace("_", "-")
            if image.ref.startswith("ghcr.io/"):
                if not image.ref.startswith(f"ghcr.io/{owner}/stellar-atlas-{role}@sha256:") or image.ref.split("@")[-1] != image.manifest_digest:
                    raise ValueError("Registry image owner/role/digest does not match source")
            elif image.local_tag != f"stellar-atlas-{role}:local-{self.source_sha[:12]}":
                raise ValueError("Local image role/source tag does not match source")
        return self


class Step(Model):
    step: Annotated[int, Field(ge=1)]
    status: Status
    detail: str
    evidence: list[str]


class Command(Model):
    command: list[str]
    exit_code: int | None
    report: str | None = None


class PhaseReport(Model):
    phase: Phase
    status: Status
    checked_at_utc: AwareDatetime
    source_commit: Commit | None
    depends_on: list[Phase]
    steps: list[Step]
    commands: list[Command]
    notes: list[str]
    human_actions: list[str]
    metadata: dict = Field(default_factory=dict)
