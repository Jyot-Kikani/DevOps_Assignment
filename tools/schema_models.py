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
    ref: Annotated[str, Field(pattern=r"^ghcr\.io/[a-z0-9-]+/stellar-atlas-(web|catalog|journey|importer)@sha256:[a-f0-9]{64}$")]
    sbom_sha256: SHA


class Images(Model):
    web: Image
    catalog: Image
    journey: Image
    importer: Image


class Compatibility(Model):
    catalog_schema: Literal[1]
    journey_schema: Literal[1]
    model: Literal["constant-speed-v1"]


class Verification(Model):
    state: Literal["pending"]


class Release(Model):
    schema_version: Literal[1]
    release_id: Annotated[str, Field(pattern=r"^r[0-9]+-a[0-9]+-[a-f0-9]{12}$")]
    source_sha: Commit
    source_repository: Annotated[str, Field(pattern=r"^[A-Za-z0-9-]+/DevOps_Assignment$")]
    created_at: AwareDatetime
    dataset: Dataset
    images: Images
    signer_identity: str
    compatibility: Compatibility
    verification: Verification

    @model_validator(mode="after")
    def consistency(self):
        if self.created_at.utcoffset().total_seconds() != 0:
            raise ValueError("Release timestamp must use UTC")
        if not self.release_id.endswith(self.source_sha[:12]):
            raise ValueError("Release suffix must match source SHA")
        expected = f"https://github.com/{self.source_repository}/.github/workflows/release.yml@refs/heads/main"
        if self.signer_identity != expected:
            raise ValueError("Signer identity does not match source repository")
        owner = self.source_repository.split("/")[0].lower()
        for role, image in self.images:
            if not image.ref.startswith(f"ghcr.io/{owner}/stellar-atlas-{role}@sha256:"):
                raise ValueError("Image owner/role does not match source")
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
