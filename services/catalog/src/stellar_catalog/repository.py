"""Read-only Catalog queries, always scoped to an explicitly ready snapshot."""
import base64
import binascii
import json
import hashlib
import math
from fastapi import HTTPException
from sqlalchemy import text
from stellar_common.ids import object_id
from stellar_common.units import radius_pc, PC_TO_LY


def snapshot(c, sid):
    row = c.execute(text("SELECT * FROM catalog.snapshots WHERE id=:s AND status='ready'"),{"s":sid}).mappings().first()
    if row is None:
        raise HTTPException(404,"Ready snapshot not found")
    p = row["provenance"]
    if c.info.get("app_env") == "demo" and p.get("fixture"):
        raise HTTPException(409,"Fixture snapshots are not available in demo mode")
    return {"snapshot_id":row["id"],"epoch":row["epoch"],"raw_sha256":row["raw_sha256"],"source_url":row["source_url"],
            "citation_urls":p["papers"],"license_url":p["license_url"],
            "counts":{"total":row["total_rows"],"within_100pc":row["in_scope_rows"],"within_50ly":p["counts"]["within_50ly"],
                      "within_25ly":p["counts"]["within_25ly"]},"max_map_radius_pc":100,"map_format_version":1,"transform_version":row["transform_version"]}


def active(c):
    sid = c.execute(text("SELECT snapshot_id FROM catalog.active_snapshot WHERE singleton=true")).scalar()
    if sid is None:
        raise HTTPException(503,"No active catalog")
    return snapshot(c,sid)


def profiles(c, sid, rows):
    ids = [r["source_id"] for r in rows]
    names = {}
    if ids:
        for source_id, alias in c.execute(text("SELECT source_id,alias FROM catalog.aliases WHERE snapshot_id=:s AND source_id=ANY(:ids) ORDER BY normalized_alias"),{"s":sid,"ids":ids}):
            names.setdefault(source_id,[]).append(alias)
    result = []
    fields = ("source_id","ordinal","distance_pc","distance_ly","distance_p16_pc","distance_p84_pc","ra_deg","dec_deg",
              "g_magnitude","bp_magnitude","rp_magnitude","color_index")
    for row in rows:
        result.append({"snapshot_id":sid,**{k:row[k] for k in fields},"position_pc":(row["x"],row["y"],row["z"]),"aliases":names.get(row["source_id"],[])})
    return result


def sun(sid):
    return {"snapshot_id":sid,"source_id":"sun","ordinal":0,"aliases":["Sun"],"position_pc":(0,0,0),"distance_pc":0,"distance_ly":0,
            **{k:None for k in ("distance_p16_pc","distance_p84_pc","ra_deg","dec_deg","g_magnitude","bp_magnitude","rp_magnitude","color_index")}}


def star(c,sid,*,id=None,ordinal=None):
    if id == "sun" or ordinal == 0:
        return sun(sid)
    column,value = ("source_id",id) if id is not None else ("ordinal",ordinal)
    row = c.execute(text(f"SELECT * FROM catalog.stars WHERE snapshot_id=:s AND {column}=:v"),{"s":sid,"v":value}).mappings().first()
    if row is None:
        raise HTTPException(404,"Object not found in this snapshot")
    return profiles(c,sid,[row])[0]


def decode_cursor(cursor,context):
    if cursor is None:
        return (-1,0,"")
    try:
        token = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor)%4)))
        if set(token) != {"context","after"} or token["context"] != context:
            raise ValueError()
        rank,distance,id = token["after"]
        if type(rank) is not int or rank not in (0,1,2) or type(distance) not in (int,float) or not math.isfinite(distance) or distance<0 or object_id(id)=="sun":
            raise ValueError()
        return rank,distance,id
    except (ValueError,TypeError,KeyError,binascii.Error,UnicodeError):
        raise HTTPException(400,"Invalid cursor for this search") from None


def search(c,sid,q,radius,limit,cursor):
    term = q.strip().casefold()
    context = hashlib.sha256(json.dumps([sid,term,float(radius),limit],separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
    rank,distance,id = decode_cursor(cursor,context)
    prefix = term.replace("\\","\\\\").replace("%","\\%").replace("_","\\_") + "%"
    params = {"s":sid,"q":term,"prefix":prefix,"r":radius_pc(radius),"rank":rank,"d":distance,"id":id,"limit":limit+1}
    if term:
        matching = """WITH candidates AS (
          SELECT source_id,0 AS rank FROM catalog.stars WHERE snapshot_id=:s AND source_id=:q
          UNION ALL SELECT source_id,1 FROM catalog.aliases WHERE snapshot_id=:s AND normalized_alias LIKE :prefix ESCAPE '\\'
          UNION ALL SELECT source_id,2 FROM catalog.stars WHERE snapshot_id=:s AND source_id LIKE :prefix ESCAPE '\\'),
          ranked AS (SELECT source_id,min(rank) AS rank FROM candidates GROUP BY source_id),
          matched AS (SELECT s.*,ranked.rank FROM catalog.stars s JOIN ranked ON ranked.source_id=s.source_id
                      WHERE s.snapshot_id=:s AND s.distance_pc<=:r)"""
    else:
        matching = "WITH matched AS (SELECT s.*,0 AS rank FROM catalog.stars s WHERE s.snapshot_id=:s AND s.distance_pc<=:r)"
    rows = c.execute(text(matching+""" SELECT * FROM matched WHERE (rank,distance_pc,source_id)>(:rank,:d,:id)
      ORDER BY rank,distance_pc,source_id LIMIT :limit"""),params).mappings().all()
    next_cursor = None
    if len(rows)>limit:
        last = rows[limit-1]
        token = {"context":context,"after":[last["rank"],last["distance_pc"],last["source_id"]]}
        next_cursor = base64.urlsafe_b64encode(json.dumps(token,separators=(",",":"),ensure_ascii=False).encode()).decode().rstrip("=")
    return {"snapshot_id":sid,"items":profiles(c,sid,rows[:limit]),"next_cursor":next_cursor}


def neighbors(c,sid,id,radius,limit):
    origin = star(c,sid,id=id)
    x,y,z = origin["position_pc"]
    rows = c.execute(text("""SELECT *, ((x-:x)^2+(y-:y)^2+(z-:z)^2) AS squared_separation
        FROM catalog.stars WHERE snapshot_id=:s AND source_id<>:id AND distance_pc<=:r
        ORDER BY squared_separation,source_id LIMIT :limit"""),
        {"x":x,"y":y,"z":z,"s":sid,"id":id,"r":radius_pc(radius),"limit":limit}).mappings().all()
    items = [{"star":p,"separation_ly":math.sqrt(r["squared_separation"])*PC_TO_LY,"distance_from_sun_ly":r["distance_ly"]}
             for r,p in zip(rows,profiles(c,sid,rows),strict=True)]
    return {"snapshot_id":sid,"origin_id":id,"radius_ly":radius,"items":items}


def map_manifest(c,sid,radius):
    metadata = snapshot(c,sid)
    r = radius_pc(radius)
    count = c.execute(text("SELECT count(*) FROM catalog.stars WHERE snapshot_id=:s AND distance_pc<=:r"),{"s":sid,"r":r}).scalar_one()
    fields = "chunk_id,count,first_ordinal,last_ordinal,min_radius_pc,max_radius_pc,uncompressed_sha256,compressed_sha256,uncompressed_bytes,compressed_bytes"
    chunks = c.execute(text(f"SELECT {fields} FROM catalog.map_chunks WHERE snapshot_id=:s AND min_radius_pc<=:r ORDER BY chunk_id"),{"s":sid,"r":r}).mappings().all()
    return {"snapshot":metadata,"radius_ly":radius,"total_count":count,"format_version":1,"record_bytes":24,
            "chunks":[{**dict(row),"url":f"/api/catalog/v1/snapshots/{sid}/chunks/{row['chunk_id']}.bin"} for row in chunks]}
