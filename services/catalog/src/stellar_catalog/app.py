from typing import Annotated
from fastapi import Header, Path, Query, Response
from .models import SnapshotID, ObjectID, Snapshot, Star, SearchResult, Neighbors, PositionsRequest, Positions, MapManifest
from .http import create_base, unavailable

app = create_base("catalog")
Radius = Annotated[float, Query(gt=0, le=326.16, allow_inf_nan=False)]
Limit = Annotated[int, Query(ge=1, le=100)]

@app.get("/v1/snapshots/active", response_model=Snapshot, operation_id="active_snapshot")
def active_snapshot():
    unavailable()

@app.get("/v1/snapshots/{snapshot}", response_model=Snapshot, operation_id="snapshot")
def snapshot_metadata(snapshot: SnapshotID):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/stars", response_model=SearchResult, operation_id="search_stars")
def stars(snapshot: SnapshotID, q: Annotated[str, Query(max_length=100)] = "", radius_ly: Radius = 25,
          limit: Limit = 20, cursor: Annotated[str | None, Query(max_length=512, pattern=r"^[A-Za-z0-9_-]+$")] = None):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/stars/{id}", response_model=Star, operation_id="star")
def star(snapshot: SnapshotID, id: ObjectID):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/ordinals/{ordinal}", response_model=Star, operation_id="ordinal")
def ordinal(snapshot: SnapshotID, ordinal: Annotated[int, Path(ge=0, le=4294967295)]):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/stars/{id}/neighbors", response_model=Neighbors, operation_id="neighbors")
def neighbors(snapshot: SnapshotID, id: ObjectID, radius_ly: Radius = 25, limit: Limit = 5):
    unavailable()

@app.post("/v1/snapshots/{snapshot}/positions", response_model=Positions, operation_id="positions", openapi_extra={"x-internal": True})
def positions(snapshot: SnapshotID, body: PositionsRequest):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/map", response_model=MapManifest, operation_id="map_manifest")
def map_manifest(snapshot: SnapshotID, radius_ly: Radius = 25):
    unavailable()

@app.get("/v1/snapshots/{snapshot}/chunks/{chunk}.bin", response_class=Response, operation_id="map_chunk", responses={
    200: {"description": "Deterministic gzip of little-endian map records", "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
          "headers": {"Content-Encoding": {"schema": {"const": "gzip"}}, "Cache-Control": {"schema": {"const": "public, max-age=31536000, immutable"}}, "ETag": {"schema": {"type": "string"}}}},
    304: {"description": "If-None-Match matches compressed byte SHA-256; no body"}})
def map_chunk(snapshot: SnapshotID, chunk: Annotated[str, Path(pattern=r"^[0-9]{6}$")],
              if_none_match: Annotated[str | None, Header(max_length=80)] = None):
    unavailable()
