from decimal import Decimal

import pytest

from fuel_control.calculations import (
    calculate_difference,
    calculate_distance,
    calculate_expected_balance,
    calculate_fuel,
    calculate_normative_consumption,
    parse_numeric_input,
)


def test_required_odometer_example():
    assert calculate_distance(234082, 236035) == Decimal("1953")


def test_required_normative_consumption_example():
    assert calculate_normative_consumption(1953, 26) == Decimal("507.78")


def test_required_expected_balance_example():
    assert calculate_expected_balance("15.79", 503, "507.78") == Decimal("11.01")


def test_winter_norm_calculation():
    assert calculate_normative_consumption(1953, "29,12") == Decimal("568.71")


def test_end_odometer_before_start_is_rejected():
    with pytest.raises(ValueError):
        calculate_distance(200, 199)


def test_missing_actual_balance_has_no_difference():
    result = calculate_fuel(234082, 236035, "15,79", 503, 26, "")
    assert result.calculated_balance == Decimal("11.01")
    assert result.difference is None


@pytest.mark.parametrize(
    ("actual", "expected"),
    [
        ("10.01", Decimal("-1.00")),
        ("12.01", Decimal("1.00")),
        ("11.01", Decimal("0.00")),
    ],
)
def test_actual_balance_reports_overspend_saving_or_match(actual, expected):
    assert calculate_difference(actual, Decimal("11.01")) == expected


def test_comma_and_dot_decimal_inputs_are_equivalent():
    assert calculate_expected_balance("15,79", "503.0", "507,78") == Decimal("11.01")


def test_numeric_input_replaces_visual_zero_instead_of_prefixing_it():
    # Calculator inputs start empty with a visual `0` placeholder, so the first
    # user-entered digits are the complete value rather than `0` + the digits.
    assert parse_numeric_input("23057", default=0) == Decimal("23057")


def test_numeric_input_accepts_comma_decimals_and_temporary_blanks():
    assert parse_numeric_input("15,79") == Decimal("15.79")
    assert parse_numeric_input("") == Decimal("0")
    assert parse_numeric_input("   ", allow_none=True) is None
