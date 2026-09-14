"""Excel export utilities."""

from io import BytesIO
import pandas as pd


def records_to_excel(records, labels: dict[str, str]) -> bytes:
    columns = ["vehicle_name", "period", "start_odometer", "end_odometer", "distance_km", "used_norm",
               "start_fuel", "refueled_fuel", "normative_consumption", "calculated_balance",
               "actual_end_fuel", "difference"]
    prepared = []
    for record in records:
        item = dict(record)
        item["period"] = f'{item["start_date"]} — {item["end_date"]}'
        prepared.append(item)
    frame = pd.DataFrame(prepared, columns=columns)
    frame.rename(columns={key: labels.get(key, key) for key in columns}, inplace=True)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=labels.get("sheet", "History"))
        sheet = writer.sheets[labels.get("sheet", "History")]
        sheet.freeze_panes, sheet.auto_filter.ref = "A2", sheet.dimensions
        for column in sheet.columns:
            sheet.column_dimensions[column[0].column_letter].width = min(
                max(len(str(cell.value or "")) for cell in column) + 2, 32
            )
    return output.getvalue()
