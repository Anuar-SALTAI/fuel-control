from io import BytesIO

import pytest


def test_excel_export():
    pytest.importorskip("pandas")
    load_workbook = pytest.importorskip("openpyxl").load_workbook
    from fuel_control.export import records_to_excel

    record = {key: value for key, value in zip(
        ["month", "vehicle_name", "season", "norm", "mileage", "filled", "opening_balance",
         "closing_balance", "normative_consumption", "actual_consumption", "difference"],
        ["2026-09", "Газель", "summer", 26, 100, 26, 0, 0, 26, 26, 0],
    )}
    content = records_to_excel([record], {"month": "Ай", "sheet": "Тарих"})
    workbook = load_workbook(BytesIO(content))
    assert workbook.sheetnames == ["Тарих"]
    assert workbook["Тарих"]["A2"].value == "2026-09"
