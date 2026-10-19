"""Allowlisted structured logging; secrets and DSN credentials are redacted."""
from datetime import datetime, timezone
import json
import logging
import re


def redact(value: str) -> str:
    value = re.sub(r"(?i)([a-z][a-z0-9+.-]*://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", value)
    return re.sub(r"(?i)\b(password|secret|token|authorization|dsn)\b\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,}]+)", r"\1=[REDACTED]", value)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {"timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                   "level": record.levelname, "message": redact(record.getMessage())}
        for key in ("service", "request_id", "route", "method", "status", "duration_ms", "source_sha"):
            if hasattr(record, key):
                value = getattr(record, key)
                payload[key] = redact(value) if isinstance(value, str) else value
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, allow_nan=False)
