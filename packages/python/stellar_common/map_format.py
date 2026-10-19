"""Version-1 24-byte map records and deterministic gzip."""
from dataclasses import dataclass
import gzip
import io
import math
import struct

from .units import finite_number, position

FORMAT_VERSION = 1
RECORD_BYTES = 24
CHUNK_RECORDS = 8192
RECORD = struct.Struct("<I5f")


@dataclass(frozen=True)
class MapRecord:
    ordinal: int
    x_pc: float
    y_pc: float
    z_pc: float
    g_mag: float | None
    bp_minus_rp: float | None


def encode(records) -> bytes:
    output = bytearray()
    for row in records:
        if isinstance(row.ordinal, bool) or not isinstance(row.ordinal, int) or not 1 <= row.ordinal <= 0xFFFFFFFF:
            raise ValueError("Catalog ordinal must be a positive uint32; zero belongs to Sun")
        xyz = position((row.x_pc, row.y_pc, row.z_pc))
        photometry = [math.nan if x is None else finite_number(x) for x in (row.g_mag, row.bp_minus_rp)]
        try:
            packed = RECORD.pack(row.ordinal, *xyz, *photometry)
        except (OverflowError, struct.error) as exc:
            raise ValueError("Record exceeds map float32 bounds") from exc
        if not all(math.isfinite(x) for x in RECORD.unpack(packed)[1:4]):
            raise ValueError("Position cannot overflow float32")
        output.extend(packed)
    return bytes(output)


def decode(data: bytes) -> list[MapRecord]:
    if len(data) % RECORD_BYTES:
        raise ValueError("Truncated map record")
    output = []
    for ordinal, x, y, z, g, color in RECORD.iter_unpack(data):
        if ordinal == 0 or not all(math.isfinite(v) for v in (x, y, z)):
            raise ValueError("Invalid ordinal or position")
        if math.isinf(g) or math.isinf(color):
            raise ValueError("Photometry may be finite or quiet NaN, never infinity")
        output.append(MapRecord(ordinal, x, y, z, None if math.isnan(g) else g, None if math.isnan(color) else color))
    return output


def deterministic_gzip(data: bytes) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=output, mode="wb", compresslevel=9, mtime=0) as zipped:
        zipped.write(data)
    return output.getvalue()
