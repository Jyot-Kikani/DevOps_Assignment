"""Validated internal service URL; credentials never belong in these URLs."""
import os
from urllib.parse import urlsplit

def internal_url(name, default):
    value = os.environ.get(name, default)
    parsed = urlsplit(value)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise ValueError(name + " must be an explicit internal base URL")
    return value
