from typing import Annotated
from uuid import UUID
from fastapi import Header
from .models import EstimateRequest, Estimate, Journey
from .http import create_base, unavailable

app = create_base("journey")

@app.post("/v1/estimate", response_model=Estimate, operation_id="estimate")
def estimate(body: EstimateRequest):
    unavailable()

@app.post("/v1/journeys", response_model=Journey, status_code=201, operation_id="create_journey", responses={
    200: {"model": Journey, "description": "Matching idempotent retry"},
    201: {"description": "Created immutable journey", "headers": {"Location": {"schema": {"type": "string"}}}}})
def create_journey(body: EstimateRequest, idempotency_key: Annotated[UUID, Header(alias="Idempotency-Key")]):
    unavailable()

@app.get("/v1/journeys/{uuid}", response_model=Journey, operation_id="journey")
def journey(uuid: UUID):
    unavailable()
