"""Common optional HTTP boundary, settings, normalized metrics and redacted logs."""
from dataclasses import dataclass
import logging
import os
import re
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from prometheus_client import CollectorRegistry, Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from .errors import request_id, error_payload
from .ids import snapshot_id
from .logging import JsonFormatter


@dataclass(frozen=True)
class Settings:
    app_env: str
    source_sha: str
    release_id: str
    snapshot_id: str

    @classmethod
    def load(cls):
        env = os.environ.get("APP_ENV", "dev")
        sha = os.environ.get("SOURCE_SHA", "")
        release = os.environ.get("RELEASE_ID", "")
        sid = snapshot_id(os.environ.get("CATALOG_SNAPSHOT_ID", ""))
        if env not in ("dev", "ci", "demo") or not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise ValueError("Configure APP_ENV and the actual 40-character SOURCE_SHA")
        if not re.fullmatch(r"(r[0-9]+-a[0-9]+-[a-f0-9]{12}|local-[a-f0-9]{12})", release) or not release.endswith(sha[:12]):
            raise ValueError("RELEASE_ID must identify the configured source commit")
        if os.environ.get("SHARE_RETENTION_DAYS", "30") != "30":
            raise ValueError("Shared records must retain the fixed 30-day policy")
        if os.environ.get("LOG_LEVEL", "INFO") not in ("DEBUG","INFO","WARNING","ERROR","CRITICAL"):
            raise ValueError("Invalid LOG_LEVEL")
        return cls(env, sha, release, sid)


def create_base(service, models, lifespan, readiness):
    errors = {status: {"model": models.ErrorResponse, "description": description} for status, description in
              {400:"Malformed query or JSON",404:"Record not found",409:"Snapshot or idempotency conflict",410:"Expired journey",
               422:"Invalid body fields",429:"Rate limit; Retry-After header",503:"Dependency unavailable"}.items()}
    app = FastAPI(title=f"Stellar Atlas {service.title()}", version="1.0.0", responses=errors, lifespan=lifespan,
                  description="Versioned local-catalog API. Immutable snapshots and anonymous constant-speed journeys.")
    app.state.service_name = service
    registry = CollectorRegistry()
    app.state.registry = registry
    app.state.requests = Counter("stellar_http_requests_total", "HTTP responses", ["service","method","route","status"], registry=registry)
    app.state.latency = Histogram("stellar_http_duration_seconds", "HTTP duration", ["service","method","route"], registry=registry)
    app.state.query_failures = Counter("stellar_database_failures_total", "Database query failures", ["service"], registry=registry)
    app.state.pool_usage = Gauge("stellar_database_pool_checked_out", "Checked-out connections", ["service"], registry=registry)
    app.state.version_info = Gauge("stellar_version_info", "Configured version identity", ["service","source_sha","snapshot"], registry=registry)
    logger = logging.getLogger("stellar." + service)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    logger.propagate = False
    app.state.logger = logger

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        started = time.perf_counter()
        request.state.request_id = request_id(request.headers.get("X-Request-ID"))
        body = bytearray()
        async for part in request.stream():
            body.extend(part[:4097-len(body)])
            if len(body) > 4096:
                return JSONResponse(error_payload("BODY_TOO_LARGE", "Body exceeds 4096 bytes", request.state.request_id),
                                    status_code=400, headers={"X-Request-ID": request.state.request_id})
        request._body = bytes(body)
        try:
            response = await call_next(request)
        except Exception:
            # Last-resort envelope: no stack trace, DSN, body or arbitrary exception text.
            logger.error("Unhandled request failure", extra={"service":service,"request_id":request.state.request_id})
            response = JSONResponse(error_payload("INTERNAL_ERROR", "Request could not be completed", request.state.request_id), status_code=500)
        response.headers["X-Request-ID"] = request.state.request_id
        route = getattr(request.scope.get("route"), "path", "unmatched")
        method = request.method if request.method in ("GET","POST","HEAD","OPTIONS") else "OTHER"
        duration = time.perf_counter()-started
        app.state.requests.labels(service,method,route,str(response.status_code)).inc()
        app.state.latency.labels(service,method,route).observe(duration)
        logger.info("request", extra={"service":service,"request_id":request.state.request_id,"route":route,"method":method,
                                      "status":response.status_code,"duration_ms":round(duration*1000,3)})
        return response

    @app.exception_handler(RequestValidationError)
    async def validation(request, exc):
        errors = exc.errors()
        status = 400 if any(e["type"] == "json_invalid" or e["loc"][0] != "body" for e in errors) else 422
        details = [{"location":list(e["loc"]),"reason":e["type"]} for e in errors]
        return JSONResponse(error_payload("INVALID_REQUEST", "Request validation failed", request.state.request_id, details), status_code=status)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        app.state.query_failures.labels(service).inc()
        return JSONResponse(error_payload("UNAVAILABLE", "Database unavailable", request.state.request_id), status_code=503)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, exc):
        codes = {404:"NOT_FOUND",409:"CONFLICT",410:"EXPIRED",429:"RATE_LIMITED",503:"UNAVAILABLE"}
        return JSONResponse(error_payload(codes.get(exc.status_code,"INVALID_REQUEST"),str(exc.detail),request.state.request_id),
                            status_code=exc.status_code,headers=exc.headers)

    @app.get("/health/live",response_model=models.Health,operation_id=f"{service}_live")
    def live():
        return {"status":"live"}

    @app.get("/health/ready",response_model=models.Health,operation_id=f"{service}_ready")
    def ready():
        healthy, _ = readiness(app)
        if not healthy:
            raise HTTPException(503,"Required database/snapshot unavailable")
        return {"status":"ready"}

    @app.get("/v1/meta",response_model=models.Meta,operation_id=f"{service}_meta")
    def meta():
        settings = getattr(app.state,"settings",None)
        if settings is None:
            raise HTTPException(503,"Service is not configured")
        healthy, active = readiness(app)
        return {"service":service,"source_sha":settings.source_sha,"release_id":settings.release_id,
                "schema_version":1,"readiness":healthy,"active_snapshot":active}

    @app.get("/metrics",response_class=PlainTextResponse,operation_id=f"{service}_metrics")
    def metrics():
        engine = getattr(app.state,"engine",None)
        if engine is not None:
            app.state.pool_usage.labels(service).set(engine.pool.checkedout())
        return Response(generate_latest(registry),media_type=CONTENT_TYPE_LATEST)
    return app
