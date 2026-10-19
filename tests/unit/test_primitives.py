import gzip
import io
import logging
import math
from pathlib import Path
import pytest
from stellar_common.ids import object_id
from stellar_common.units import distance_pc, estimate, travel_years, speed_km_s, scene_position, radius_pc, JULIAN_YEAR_SECONDS
from stellar_common.map_format import MapRecord, encode, decode, deterministic_gzip
from stellar_common.logging import JsonFormatter

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_triangle_and_sun_independent_oracles():
    result = estimate((0, 0, 0), (3, 4, 0), 0.1)
    assert result["distance_pc"] == 5
    assert result["distance_ly"] == pytest.approx(16.307818885)
    assert result["duration_julian_years"] == pytest.approx(163.07818885)
    assert result["speed_km_s"] == pytest.approx(29979.2458)
    assert travel_years(0.1, 0.1) == 1
    assert JULIAN_YEAR_SECONDS == 31557600
    assert distance_pc((0, 0, 0), (1e-9, 0, 0)) == 1e-9
    assert distance_pc((1, 2, 3), (1, 2, 3)) == 0


@pytest.mark.parametrize("value", [0.001, 0.5])
def test_speed_boundaries(value):
    assert speed_km_s(value) > 0


@pytest.mark.parametrize("value", [0, 0.000999, 0.500001, math.nan, math.inf, -math.inf, True, "0.1"])
def test_invalid_speed(value):
    with pytest.raises(ValueError):
        speed_km_s(value)


def test_ids_and_units():
    assert object_id("5853498713190525696") == "5853498713190525696"
    for value in (5853498713190525696, "-1", "1e19", "1" * 21, "", True):
        with pytest.raises(ValueError):
            object_id(value)
    assert object_id("sun") == "sun"
    assert radius_pc(326.16) == 100
    assert scene_position((0, 1, 0)) == (0, 0, -1)
    assert scene_position((0, 0, 1)) == (0, 1, 0)
    with pytest.raises(ValueError):
        distance_pc((math.inf, 0, 0), (0, 0, 0))


def test_golden_and_gzip():
    golden = (FIXTURES / "map/golden.bin").read_bytes()
    records = [MapRecord(1, 1, 2, 3, 4, 5), MapRecord(2, 0, -1, 0.5, None, None)]
    assert encode(records) == golden
    assert decode(golden) == records
    first = deterministic_gzip(golden)
    assert first == deterministic_gzip(golden)
    assert first[4:8] == b"\0\0\0\0"
    assert gzip.decompress(first) == golden
    for invalid in (b"x", bytes(24)):
        with pytest.raises(ValueError):
            decode(invalid)
    with pytest.raises(ValueError):
        encode([MapRecord(1, math.inf, 0, 0, None, None)])


def test_redacted_logs():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.Logger("test")
    logger.addHandler(handler)
    logger.error("postgresql://fixture:do-not-retain@localhost/db password=fixture-only token=fixture-only",
                 extra={"request_id": "test-1", "unapproved": "hidden"})
    value = stream.getvalue()
    assert "do-not-retain" not in value and "fixture-only" not in value and "hidden" not in value
    assert "test-1" in value
