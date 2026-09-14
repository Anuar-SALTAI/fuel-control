"""Excel export utilities."""

from io import BytesIO

import pandas as pd


def records_to_excel(records, labels: dict[str, str]) -> bytes:
    columns = [
        "month", "vehicle_name", "season", "norm", "mileage", "filled",
        "opening_balance", "closing_balance", "normative_consumption",
        "actual_consumption", "difference",
    ]
    frame = pd.DataFrame([dict(row) for row in records], columns=columns)
    frame.rename(columns={key: labels.get(key, key) for key in columns}, inplace=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=labels.get("sheet", "History"))
        sheet = writer.sheets[labels.get("sheet", "History")]
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for column in sheet.columns:
            width = min(max(len(str(cell.value or "")) for cell in column) + 2, 30)
            sheet.column_dimensions[column[0].column_letter].width = width
    return output.getvalue()
