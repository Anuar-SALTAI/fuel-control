"""Pure, UI-independent fuel calculations."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ZERO_TOLERANCE = Decimal("0.005")


def as_decimal(value: Decimal | float | int | str) -> Decimal:
    """Parse numbers consistently, accepting either comma or dot decimals."""
    if isinstance(value, str):
        value = value.strip().replace(" ", "").replace(",", ".")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Invalid numeric value") from error


def round_fuel(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_distance(start_odometer, end_odometer) -> Decimal:
    start, end = as_decimal(start_odometer), as_decimal(end_odometer)
    if start < 0 or end < 0:
        raise ValueError("Odometer values cannot be negative")
    if end < start:
        raise ValueError("End odometer cannot be less than start odometer")
    return end - start


def calculate_normative_consumption(distance_km, fuel_norm) -> Decimal:
    distance, norm = as_decimal(distance_km), as_decimal(fuel_norm)
    if distance < 0 or norm < 0:
        raise ValueError("Distance and norm cannot be negative")
    return round_fuel(distance * norm / Decimal(100))


def calculate_expected_balance(start_fuel, refueled_fuel, normative_consumption) -> Decimal:
    start, refueled, consumption = map(as_decimal, (start_fuel, refueled_fuel, normative_consumption))
    if start < 0 or refueled < 0 or consumption < 0:
        raise ValueError("Fuel values cannot be negative")
    return round_fuel(start + refueled - consumption)


def calculate_difference(actual_end_fuel, calculated_balance) -> Decimal | None:
    if actual_end_fuel is None or (isinstance(actual_end_fuel, str) and not actual_end_fuel.strip()):
        return None
    actual = as_decimal(actual_end_fuel)
    if actual < 0:
        raise ValueError("Actual balance cannot be negative")
    difference = round_fuel(actual - as_decimal(calculated_balance))
    return Decimal("0.00") if abs(difference) < ZERO_TOLERANCE else difference


@dataclass(frozen=True)
class FuelCalculation:
    distance_km: Decimal
    normative_consumption: Decimal
    calculated_balance: Decimal
    difference: Decimal | None


def calculate_fuel(start_odometer, end_odometer, start_fuel, refueled_fuel, fuel_norm, actual_end_fuel=None):
    distance = calculate_distance(start_odometer, end_odometer)
    consumption = calculate_normative_consumption(distance, fuel_norm)
    balance = calculate_expected_balance(start_fuel, refueled_fuel, consumption)
    return FuelCalculation(distance, consumption, balance, calculate_difference(actual_end_fuel, balance))
