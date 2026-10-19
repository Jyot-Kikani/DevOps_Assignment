"""Contract boundary only. Feature handlers are implemented in P06/P07."""
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from stellar_common.errors import request_id, error_payload
from .models import ErrorResponse, Health, Meta

ERRORS = {status: {"model": ErrorResponse, "description": description}
          for status, description in {400: "Malformed query or JSON", 404: "Record not found",
              409: "Snapshot or idempotency conflict", 410: "Expired journey", 422: "Invalid body fields",
              429: "Rate limit; Retry-After header", 503: "Dependency unavailable"}.items()}

def unavailable():
    raise HTTPException(503, "Feature dependency is not implemented in this phase")

def create_base(service):
    app = FastAPI(title=f"Stellar Atlas {service.title()}", version="1.0.0", responses=ERRORS,
                  description="Contract scaffold. Data handlers deliberately return 503 until their implementation phase.")

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        request.state.request_id = request_id(request.headers.get("X-Request-ID"))
        # Read at most 4097 bytes; never buffer an unbounded chunked request.
        body = bytearray()
        async for part in request.stream():
            body.extend(part[:4097 - len(body)])
            if len(body) > 4096:
                return JSONResponse(error_payload("BODY_TOO_LARGE", "Body exceeds 4096 bytes", request.state.request_id),
                                    status_code=400, headers={"X-Request-ID": request.state.request_id})
        request._body = bytes(body)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        errors = exc.errors()
        status = 400 if any(e["type"] == "json_invalid" or e["loc"][0] != "body" for e in errors) else 422
        details = [{"location": list(e["loc"]), "reason": e["type"]} for e in errors]
        return JSONResponse(error_payload("INVALID_REQUEST", "Request validation failed", request.state.request_id, details), status_code=status)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        codes = {404: "NOT_FOUND", 409: "CONFLICT", 410: "EXPIRED", 429: "RATE_LIMITED", 503: "UNAVAILABLE"}
        return JSONResponse(error_payload(codes.get(exc.status_code, "INVALID_REQUEST"),
                            str(exc.detail), request.state.request_id), status_code=exc.status_code, headers=exc.headers)

    @app.get("/health/live", response_model=Health, operation_id=f"{service}_live")
    def live():
        return {"status": "live"}

    @app.get("/health/ready", response_model=Health, operation_id=f"{service}_ready")
    def ready():
        unavailable()

    @app.get("/v1/meta", response_model=Meta, operation_id=f"{service}_meta")
    def meta():
        unavailable()  # No invented image SHA, release ID, or readiness.

    @app.get("/metrics", response_class=PlainTextResponse, operation_id=f"{service}_metrics")
    def metrics():
        unavailable()
    return app
