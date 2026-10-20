"""Only HTTP crosses the service boundary; no Catalog package/database imports."""
import asyncio
import json
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from stellar_common.units import estimate
from .models import CatalogPositions


async def calculate(app,body,request_id):
    client = getattr(app.state,"catalog_client",None)
    if client is None:
        raise HTTPException(503,"Catalog connection is not configured")
    result = None
    try:
        # HTTPX phase timeouts alone are not a total deadline. This caps both attempts.
        async with asyncio.timeout(3):
            for attempt in range(2):
                try:
                    async with client.stream("POST",f"/v1/snapshots/{body.snapshot_id}/positions",
                            json={"ids":[body.origin_id,body.destination_id]},headers={"X-Request-ID":request_id}) as response:
                        app.state.logger.info("catalog_positions",extra={"service":"journey","request_id":request_id,
                            "route":"/v1/snapshots/{snapshot}/positions","status":response.status_code})
                        if response.status_code==503 and attempt==0:
                            continue
                        if response.status_code in (404,409):
                            raise HTTPException(response.status_code,"Catalog snapshot or object unavailable")
                        if response.status_code!=200:
                            raise HTTPException(503,"Catalog dependency unavailable")
                        data = bytearray()
                        async for part in response.aiter_bytes():
                            data.extend(part[:4097-len(data)])
                            if len(data)>4096:
                                raise HTTPException(503,"Catalog response exceeds its contract")
                        result = CatalogPositions.model_validate(json.loads(data))
                        break
                except (httpx.ConnectError,httpx.ReadError,httpx.ConnectTimeout):
                    if attempt:
                        raise HTTPException(503,"Catalog connection unavailable") from None
    except (TimeoutError,httpx.TimeoutException,httpx.TransportError):
        raise HTTPException(503,"Catalog request timed out or failed") from None
    except (ValueError,ValidationError):
        raise HTTPException(503,"Catalog response violates its contract") from None
    if result is None:
        raise HTTPException(503,"Catalog dependency unavailable")
    if result.snapshot_id!=body.snapshot_id:
        raise HTTPException(409,"Catalog returned an incompatible snapshot")
    positions = {row.source_id:row.position_pc for row in result.items}
    if len(positions)!=2 or set(positions)!={body.origin_id,body.destination_id}:
        raise HTTPException(503,"Catalog returned unexpected objects")
    origin,destination = positions[body.origin_id],positions[body.destination_id]
    try:
        return {**body.model_dump(),"origin_position_pc":origin,"destination_position_pc":destination,
                **estimate(origin,destination,body.speed_fraction_c)}
    except ValueError:
        raise HTTPException(503,"Catalog positions cannot produce a finite calculation") from None
