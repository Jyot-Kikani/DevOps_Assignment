from fastapi import Request
from stellar_common.api import create_base
from . import models
from .catalog import calculate
from .runtime import lifespan, readiness

app = create_base("calculation", models, lifespan, readiness)

@app.post("/v1/estimate", response_model=models.Estimate, operation_id="estimate")
async def estimate(body: models.EstimateRequest, request: Request):
    return await calculate(app, body, request.state.request_id)
