from typing import Annotated
from fastapi import Header, HTTPException, Path, Query, Response
from sqlalchemy import text
from stellar_common.api import create_base
from . import models, repository as repo
from .models import SnapshotID, ObjectID, Snapshot, Star, SearchResult, Neighbors, PositionsRequest, Positions, MapManifest
from .runtime import lifespan, readiness



def create_app(service):
    app = create_base(service, models, lifespan, readiness)
    Radius = Annotated[float,Query(gt=0,le=326.16,allow_inf_nan=False)]
    Limit = Annotated[int,Query(ge=1,le=100)]

    def connection():
        engine = getattr(app.state,"engine",None)
        if engine is None:
            raise HTTPException(503,"Service is not configured")
        c = engine.connect()
        c.info["app_env"] = app.state.settings.app_env
        return c

    if service == 'snapshot':
        @app.get("/v1/snapshots/active",response_model=Snapshot,operation_id="active_snapshot")
        def active_snapshot():
            with connection() as c:
                return repo.active(c)

    if service == 'snapshot':
        @app.get("/v1/snapshots/{snapshot}",response_model=Snapshot,operation_id="snapshot")
        def snapshot_metadata(snapshot:SnapshotID):
            with connection() as c:
                return repo.snapshot(c,snapshot)

    if service == 'search':
        @app.get("/v1/snapshots/{snapshot}/stars",response_model=SearchResult,operation_id="search_stars")
        def stars(snapshot:SnapshotID,q:Annotated[str,Query(max_length=100)]="",radius_ly:Radius=25,limit:Limit=20,
                  cursor:Annotated[str|None,Query(max_length=512,pattern=r"^[A-Za-z0-9_-]+$")]=None):
            with connection() as c:
                repo.snapshot(c,snapshot)
                return repo.search(c,snapshot,q,radius_ly,limit,cursor)

    if service == 'catalog':
        @app.get("/v1/snapshots/{snapshot}/stars/{id}",response_model=Star,operation_id="star")
        def star(snapshot:SnapshotID,id:ObjectID):
            with connection() as c:
                repo.snapshot(c,snapshot)
                return repo.star(c,snapshot,id=id)

    if service == 'catalog':
        @app.get("/v1/snapshots/{snapshot}/ordinals/{ordinal}",response_model=Star,operation_id="ordinal")
        def ordinal(snapshot:SnapshotID,ordinal:Annotated[int,Path(ge=0,le=4294967295)]):
            with connection() as c:
                repo.snapshot(c,snapshot)
                return repo.star(c,snapshot,ordinal=ordinal)

    if service == 'search':
        @app.get("/v1/snapshots/{snapshot}/stars/{id}/neighbors",response_model=Neighbors,operation_id="neighbors")
        def neighbors(snapshot:SnapshotID,id:ObjectID,radius_ly:Radius=25,limit:Limit=5):
            with connection() as c:
                repo.snapshot(c,snapshot)
                return repo.neighbors(c,snapshot,id,radius_ly,limit)

    if service == 'catalog':
        @app.post("/v1/snapshots/{snapshot}/positions",response_model=Positions,operation_id="positions",openapi_extra={"x-internal":True})
        def positions(snapshot:SnapshotID,body:PositionsRequest):
            with connection() as c:
                repo.snapshot(c,snapshot)
                return {"snapshot_id":snapshot,"items":[{"source_id":id,"position_pc":repo.star(c,snapshot,id=id)["position_pc"]} for id in body.ids]}

    if service == 'atlas_map':
        @app.get("/v1/snapshots/{snapshot}/map",response_model=MapManifest,operation_id="map_manifest")
        def map_manifest(snapshot:SnapshotID,radius_ly:Radius=25):
            with connection() as c:
                return repo.map_manifest(c,snapshot,radius_ly)

    if service == 'atlas_map':
        @app.get("/v1/snapshots/{snapshot}/chunks/{chunk}.bin",response_class=Response,operation_id="map_chunk",responses={
            200:{"description":"Deterministic gzip of little-endian map records","content":{"application/octet-stream":{"schema":{"type":"string","format":"binary"}}},
                 "headers":{"Content-Encoding":{"schema":{"const":"gzip"}},"Cache-Control":{"schema":{"const":"public, max-age=31536000, immutable"}},"ETag":{"schema":{"type":"string"}}}},
            304:{"description":"If-None-Match matches compressed byte SHA-256; no body"}})
        def map_chunk(snapshot:SnapshotID,chunk:Annotated[str,Path(pattern=r"^[0-9]{6}$")],
                      if_none_match:Annotated[str|None,Header(max_length=80)]=None):
            with connection() as c:
                repo.snapshot(c,snapshot)
                row = c.execute(text("SELECT gzip,compressed_sha256 FROM catalog.map_chunks WHERE snapshot_id=:s AND chunk_id=:c"),{"s":snapshot,"c":chunk}).mappings().first()
                if row is None:
                    raise HTTPException(404,"Map chunk not found")
                etag = '"' + row["compressed_sha256"] + '"'
                headers = {"Cache-Control":"public, max-age=31536000, immutable","ETag":etag,"Content-Encoding":"gzip"}
                if if_none_match is not None and (if_none_match.removeprefix("W/") == etag or if_none_match == "*"):
                    return Response(status_code=304,headers=headers)
                return Response(row["gzip"],media_type="application/octet-stream",headers=headers)

    return app
