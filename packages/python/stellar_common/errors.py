"""Public error envelope and bounded request identifiers."""
import re
from uuid import uuid4

from .ids import REQUEST_ID_PATTERN


def request_id(value=None):
    return value if isinstance(value, str) and re.fullmatch(REQUEST_ID_PATTERN, value) else uuid4().hex


def error_payload(code, message, identifier=None, details=None):
    return {"error": {"code": code, "message": message,
                      "request_id": request_id(identifier), "details": details or []}}
