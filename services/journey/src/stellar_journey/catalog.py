"""Journey calls Calculation over HTTP; scientific logic lives there."""
import asyncio
import httpx
from fastapi import HTTPException
from pydantic import ValidationError
from .models import Estimate

async def calculate(app, body, request_id):
    client = getattr(app.state, "calculation_client", None)
    if client is None:
        raise HTTPException(503, "Calculation connection is not configured")
    try:
        async with asyncio.timeout(5):
            response = await client.post("/v1/estimate", json=body.model_dump(),
                                         headers={"X-Request-ID": request_id})
        if response.status_code in (404, 409):
            raise HTTPException(response.status_code, "Calculation snapshot or object unavailable")
        if response.status_code != 200:
            raise HTTPException(503, "Calculation dependency unavailable")
        result = Estimate.model_validate(response.json())
    except (TimeoutError, httpx.TransportError):
        raise HTTPException(503, "Calculation request timed out or failed") from None
    except (ValueError, ValidationError):
        raise HTTPException(503, "Calculation response violates its contract") from None
    if any(getattr(result, field) != value for field, value in body.model_dump().items()):
        raise HTTPException(409, "Calculation returned incompatible inputs")
    return result.model_dump()
