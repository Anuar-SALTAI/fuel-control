"""Pure fuel-consumption calculations."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


def _decimal(value: float | int | str) -> Decimal:
    return Decimal(str(value))


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class FuelCalculation:
    normative_consumption: float
    actual_consumption: float
    difference: float

    @property
    def is_saving(self) -> bool:
        return self.difference >= 0


def calculate_fuel(
    mileage: float, norm: float, filled: float, opening_balance: float, closing_balance: float
) -> FuelCalculation:
    """Calculate normative/actual use and savings (negative means overspending)."""
    values = (mileage, norm, filled, opening_balance, closing_balance)
    if any(_decimal(value) < 0 for value in values):
        raise ValueError("Fuel inputs cannot be negative")

    normative = _decimal(mileage) * _decimal(norm) / Decimal(100)
    actual = _decimal(opening_balance) + _decimal(filled) - _decimal(closing_balance)
    if actual < 0:
        raise ValueError("Closing balance cannot exceed available fuel")
    difference = normative - actual
    return FuelCalculation(_round(normative), _round(actual), _round(difference))
