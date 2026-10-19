"""Float64 constant-speed calculations in the catalog/Sun frame."""
import math

PC_TO_LY = 3.261563777
C_KM_S = 299792.458
JULIAN_YEAR_SECONDS = 31557600
MODEL_VERSION = "constant-speed-v1"
ASSUMPTIONS = "Straight path at constant speed in the Sun/catalog frame; excludes acceleration, gravity and relativity."


def finite_number(value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("A finite numeric value is required")
    return float(value)


def position(value) -> tuple[float, float, float]:
    if len(value) != 3:
        raise ValueError("A position has exactly three coordinates")
    return tuple(finite_number(v) for v in value)


def distance_pc(origin, destination) -> float:
    result = math.dist(position(origin), position(destination))
    if not math.isfinite(result):
        raise ValueError("Distance overflow")
    return result


def parsecs_to_light_years(value) -> float:
    result = finite_number(value) * PC_TO_LY
    if result < 0 or not math.isfinite(result):
        raise ValueError("Distance must be nonnegative and finite")
    return result


def speed_km_s(fraction) -> float:
    fraction = finite_number(fraction)
    if not 0.001 <= fraction <= 0.5:
        raise ValueError("Speed must be between 0.001c and 0.5c")
    return fraction * C_KM_S


def travel_years(distance_ly, fraction) -> float:
    distance = finite_number(distance_ly)
    speed_km_s(fraction)
    if distance < 0:
        raise ValueError("Distance must be nonnegative")
    result = distance / fraction
    if not math.isfinite(result):
        raise ValueError("Journey duration overflow")
    return result


def estimate(origin, destination, fraction) -> dict:
    separation = distance_pc(origin, destination)
    light_years = parsecs_to_light_years(separation)
    return {"distance_pc": separation, "distance_ly": light_years,
            "speed_fraction_c": finite_number(fraction), "speed_km_s": speed_km_s(fraction),
            "duration_julian_years": travel_years(light_years, fraction),
            "model_version": MODEL_VERSION, "assumptions": [ASSUMPTIONS]}


def radius_pc(radius_ly) -> float:
    value = finite_number(radius_ly)
    if not 0 < value <= 326.16:
        raise ValueError("Radius is outside the supported neighborhood")
    return 100.0 if value == 326.16 else value / PC_TO_LY


def scene_position(galactic):
    x, y, z = position(galactic)
    return x, z, -y
