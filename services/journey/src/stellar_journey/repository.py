from datetime import timedelta
import hashlib
import json
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .db import journeys


def request_hash(body):
    return hashlib.sha256(json.dumps(body.model_dump(),sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def by_key(engine,key):
    with engine.connect() as c:
        row = c.execute(select(journeys).where(journeys.c.idempotency_key==key)).mappings().first()
        return dict(row) if row else None


def visible(row,now):
    if row is None:
        raise HTTPException(404,"Journey not found")
    if now>=row["expires_at"]+timedelta(days=7):
        raise HTTPException(404,"Journey retention has elapsed")
    if now>=row["expires_at"]:
        raise HTTPException(410,"Journey expired after 30 days")
    return {k:v for k,v in row.items() if k not in ("idempotency_key","request_hash")}


def check_retry(row,hash,now):
    if row["request_hash"]!=hash:
        raise HTTPException(409,"Idempotency key already used with different inputs")
    return visible(row,now)


def create(engine,key,hash,calculation,now):
    values = {**calculation,"id":uuid4(),"idempotency_key":key,"request_hash":hash,
              "created_at":now,"expires_at":now+timedelta(days=30)}
    with engine.begin() as c:
        row = c.execute(insert(journeys).values(**values).on_conflict_do_nothing(index_elements=[journeys.c.idempotency_key]).returning(journeys)).mappings().first()
        if row:
            return visible(dict(row),now),True
        # READ COMMITTED gives this statement a new snapshot after a concurrent insert commits.
        row = c.execute(select(journeys).where(journeys.c.idempotency_key==key)).mappings().one()
        return check_retry(dict(row),hash,now),False


def get(engine,id,now):
    with engine.connect() as c:
        row = c.execute(select(journeys).where(journeys.c.id==id)).mappings().first()
        return visible(dict(row) if row else None,now)
