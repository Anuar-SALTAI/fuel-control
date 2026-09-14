from pathlib import Path

from fuel_control.i18n import TEXT


def test_kazakh_uses_juris_terminology_everywhere():
    assert TEXT["kk"]["start_odometer"] == "Бастапқы жүріс, км"
    assert TEXT["kk"]["end_odometer"] == "Соңғы жүріс, км"
    assert TEXT["kk"]["distance_km"] == "Жүрілген қашықтық, км"
    assert "пробег" not in " ".join(
        value for value in TEXT["kk"].values() if isinstance(value, str)
    ).lower()


def test_russian_odometer_labels_include_units():
    assert TEXT["ru"]["start_odometer"] == "Начальный пробег, км"
    assert TEXT["ru"]["end_odometer"] == "Конечный пробег, км"
    assert TEXT["ru"]["distance_km"] == "Пройденное расстояние, км"


def test_layout_reserves_space_below_streamlit_header():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "padding:3.75rem 1.5rem 3rem" in source
    assert "safe-area-inset-top" in source
