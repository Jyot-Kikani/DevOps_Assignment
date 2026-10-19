"""Preserve Gaia identifiers as decimal strings, including values above 2**53."""
import re

ID_PATTERN = r"^(sun|[0-9]{1,20})$"
SNAPSHOT_PATTERN = r"^[a-z0-9][a-z0-9-]{0,95}$"
REQUEST_ID_PATTERN = r"^[A-Za-z0-9._-]{1,64}$"


def object_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(ID_PATTERN, value):
        raise ValueError("Object ID must be sun or a decimal string of 1–20 digits")
    return value


def snapshot_id(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(SNAPSHOT_PATTERN, value):
        raise ValueError("Invalid snapshot identifier")
    return value
