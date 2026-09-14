import pytest

from fuel_control.calculations import calculate_fuel


def test_summer_gazelle_calculation():
    result = calculate_fuel(1000, 26, 250, 20, 10)
    assert result.normative_consumption == 260
    assert result.actual_consumption == 260
    assert result.difference == 0
    assert result.is_saving


def test_winter_gazelle_uses_decimal_norm_and_reports_saving():
    result = calculate_fuel(1250, 29.12, 300, 50, 20)
    assert result.normative_consumption == 364
    assert result.actual_consumption == 330
    assert result.difference == 34


def test_overspending_is_negative():
    result = calculate_fuel(100, 26, 30, 10, 5)
    assert result.difference == -9
    assert not result.is_saving


@pytest.mark.parametrize("values", [(-1, 26, 0, 0, 0), (1, -26, 0, 0, 0)])
def test_negative_inputs_are_rejected(values):
    with pytest.raises(ValueError):
        calculate_fuel(*values)


def test_impossible_balance_is_rejected():
    with pytest.raises(ValueError):
        calculate_fuel(100, 26, 5, 5, 11)
