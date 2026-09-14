from io import BytesIO

import pytest


def test_excel_export():
    pytest.importorskip("pandas")
    load_workbook = pytest.importorskip("openpyxl").load_workbook
    from fuel_control.export import records_to_excel

    record = dict(vehicle_name="Газель", start_date="2026-09-01", end_date="2026-09-07",
                  start_odometer=100, end_odometer=200, distance_km=100, used_norm=26,
                  start_fuel=10, refueled_fuel=20, normative_consumption=26,
                  calculated_balance=4, actual_end_fuel=None, difference=None)
    content = records_to_excel([record], {"vehicle_name": "Автокөлік", "sheet": "Тарих"})
    workbook = load_workbook(BytesIO(content))
    assert workbook.sheetnames == ["Тарих"]
    assert workbook["Тарих"]["A2"].value == "Газель"
    assert workbook["Тарих"]["B2"].value == "2026-09-01 — 2026-09-07"
