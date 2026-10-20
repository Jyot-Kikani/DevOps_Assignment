from typing import Annotated
from uuid import UUID
from fastapi import Header, HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from stellar_common.api import create_base
from . import models, repository as repo
from .models import EstimateRequest, Estimate, Journey
from .runtime import lifespan, readiness
from .catalog import calculate

app = create_base("journey",models,lifespan,readiness)


def engine():
    value = getattr(app.state,"engine",None)
    if value is None:
        raise HTTPException(503,"Service is not configured")
    return value


@app.post("/v1/estimate",response_model=Estimate,operation_id="estimate")
async def estimate(body:EstimateRequest,request:Request):
    return await calculate(app,body,request.state.request_id)


@app.post("/v1/journeys",response_model=Journey,status_code=201,operation_id="create_journey",responses={
    200:{"model":Journey,"description":"Matching idempotent retry"},
    201:{"description":"Created immutable journey","headers":{"Location":{"schema":{"type":"string"}}}}})
async def create_journey(body:EstimateRequest,idempotency_key:Annotated[UUID,Header(alias="Idempotency-Key")],request:Request,response:Response):
    db = engine()
    hash = repo.request_hash(body)
    row = await run_in_threadpool(repo.by_key,db,idempotency_key)
    if row is not None:
        result = repo.check_retry(row,hash,app.state.clock())
        created = False
    else:
        calculation = await calculate(app,body,request.state.request_id)
        result,created = await run_in_threadpool(repo.create,db,idempotency_key,hash,calculation,app.state.clock())
    response.status_code = 201 if created else 200
    response.headers["Location"] = f"/v1/journeys/{result['id']}"
    return result


@app.get("/v1/journeys/{uuid}",response_model=Journey,operation_id="journey")
def journey(uuid:UUID):
    return repo.get(engine(),uuid,app.state.clock())
