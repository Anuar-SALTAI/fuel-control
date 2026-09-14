"""Responsive Streamlit dashboard for odometer-based fuel accounting."""

import html
import sqlite3
from datetime import date
from decimal import Decimal

import streamlit as st

from fuel_control.calculations import as_decimal, calculate_fuel
from fuel_control.database import Database
from fuel_control.export import records_to_excel
from fuel_control.i18n import TEXT

st.set_page_config(
    page_title="Fuel Control",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(
    """<style>
:root{--fc-blue:#0868df;--fc-navy:#102a56;--fc-border:#dbe6f2;--fc-bg:#f5f8fc}
.stApp{background:linear-gradient(135deg,#f7faff 0%,#fff 52%,#f4f8fd 100%);color:var(--fc-navy)}
.block-container{max-width:1280px;padding:3.75rem 1.5rem 3rem}.fc-brand{font-size:1.48rem;font-weight:800;color:#0b2348}
.fc-subtitle{color:#60738f;font-size:.88rem}.fc-page-title{font-size:1.75rem;font-weight:800;margin:.8rem 0 .05rem}
.fc-page-note{color:#60738f;margin-bottom:1.1rem}.fc-card{background:#fff;border:1px solid var(--fc-border);border-radius:12px;
padding:1.15rem;box-shadow:0 2px 10px rgba(34,75,120,.035);margin-bottom:1rem}.fc-card-title{font-size:1.05rem;font-weight:750;margin-bottom:.9rem}
.fc-result{min-height:122px;border-radius:11px;padding:1rem;background:#edf7ff;color:#155ea8}.fc-result.orange{background:#fff3e6;color:#9d4a00}
.fc-result.purple{background:#f4efff;color:#5833b8}.fc-result.green{background:#eafaf1;color:#087240}.fc-label{font-size:.82rem;font-weight:650}
.fc-value{font-size:1.65rem;font-weight:800;margin:.3rem 0}.fc-formula{font-size:.78rem;opacity:.72}.fc-status{border-radius:10px;padding:.9rem;background:#f6f9fd;text-align:center}
.fc-vehicle{border:1px solid var(--fc-border);border-radius:10px;padding:.8rem;margin:.5rem 0;background:#fff}.fc-vehicle b{font-size:.98rem}
.fc-badge{float:right;background:#daf6e3;color:#08733b;border-radius:999px;padding:.18rem .55rem;font-size:.72rem}.fc-badge.off{background:#edf0f4;color:#667085}
.fc-table-wrap{overflow-x:auto}.fc-table{width:100%;border-collapse:collapse;font-size:.78rem}.fc-table th{background:#eaf0f7;color:#435673;text-align:left}
.fc-table th,.fc-table td{padding:.55rem;border:1px solid #dce5ef;white-space:nowrap}.fc-mobile-records{display:none}.fc-mobile-record{background:#fff;border:1px solid var(--fc-border);border-radius:10px;padding:.8rem;margin:.55rem 0}
section[data-testid="stSidebar"]{background:#f7faff;border-right:1px solid var(--fc-border)}
section[data-testid="stSidebar"] [role="radiogroup"] label{padding:.48rem .6rem;border-radius:8px;margin:.15rem 0}
div[data-testid="stButton"] button,div[data-testid="stDownloadButton"] button{border-radius:8px;min-height:2.65rem;font-weight:650}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,textarea{border-radius:8px!important}
@media(max-width:700px){.block-container{padding:calc(3.75rem + env(safe-area-inset-top, 0px)) .65rem 2rem}.fc-brand{font-size:1.2rem}.fc-page-title{font-size:1.45rem}
.fc-result{min-height:104px;padding:.75rem}.fc-value{font-size:1.3rem}.fc-table-wrap{display:none}.fc-mobile-records{display:block}
div[data-testid="stHorizontalBlock"]{gap:.55rem}.fc-card{padding:.8rem}.fc-vehicle .fc-badge{float:none;display:inline-block;margin-top:.35rem}}
</style>""",
    unsafe_allow_html=True,
)

db = Database()
header, switch = st.columns([5, 1.2], vertical_alignment="center")
header.markdown(
    '<div class="fc-brand">⛽ Fuel Control</div><div class="fc-subtitle">Автокөлік жанармай есебі / Учет топлива автомобилей</div>',
    unsafe_allow_html=True,
)
language = switch.radio(
    "Language", ["Қаз", "Рус"], horizontal=True, label_visibility="collapsed"
)
t = TEXT["kk" if language == "Қаз" else "ru"]

menu_labels = [
    t["new_calculation"],
    t["history"],
    t["vehicles"],
    t["excel_export"],
    t["settings"],
    t["instruction"],
]
page = st.sidebar.radio("Fuel Control", menu_labels, label_visibility="collapsed")
st.sidebar.caption("v1.1.0")


def fmt(value: Decimal | float, unit="л") -> str:
    return f"{Decimal(str(value)):.2f} {unit}"


def metric_card(label, value, formula, color=""):
    return f'<div class="fc-result {color}"><div class="fc-label">{html.escape(label)}</div><div class="fc-value">{html.escape(value)}</div><div class="fc-formula">{html.escape(formula)}</div></div>'


def page_heading(title, note):
    st.markdown(
        f'<div class="fc-page-title">{html.escape(title)}</div><div class="fc-page-note">{html.escape(note)}</div>',
        unsafe_allow_html=True,
    )


def export_labels():
    return {
        "vehicle_name": t["vehicle_name"],
        "period": t["period_export"],
        "start_odometer": t["start_odometer"],
        "end_odometer": t["end_odometer"],
        "distance_km": t["distance_km"],
        "used_norm": t["norm_unit"],
        "start_fuel": t["start_fuel_export"],
        "refueled_fuel": t["refueled_fuel_export"],
        "normative_consumption": t["normative_consumption"],
        "calculated_balance": t["calculated_balance"],
        "actual_end_fuel": t["actual_end_fuel_export"],
        "difference": t["difference"],
        "sheet": t["sheet"],
    }


def recent_records(records):
    if not records:
        st.info(t["no_history"])
        return
    headers = [
        t[key]
        for key in (
            "date",
            "vehicle",
            "odometer_range",
            "distance_short",
            "used_norm",
            "expense",
            "start_balance_short",
            "refueled_short",
            "expected_short",
            "actual_short",
            "difference",
            "note",
        )
    ]
    rows = []
    cards = []
    for row in records[:5]:
        values = [
            row["end_date"],
            row["vehicle_name"],
            f'{row["start_odometer"]:g} → {row["end_odometer"]:g}',
            f'{row["distance_km"]:g}',
            f'{row["used_norm"]:.2f}',
            f'{row["normative_consumption"]:.2f}',
            f'{row["start_fuel"]:.2f}',
            f'{row["refueled_fuel"]:.2f}',
            f'{row["calculated_balance"]:.2f}',
            "—" if row["actual_end_fuel"] is None else f'{row["actual_end_fuel"]:.2f}',
            "—" if row["difference"] is None else f'{row["difference"]:+.2f}',
            row["note"] or "—",
        ]
        rows.append(
            "<tr>"
            + "".join(f"<td>{html.escape(str(value))}</td>" for value in values)
            + "</tr>"
        )
        cards.append(
            f'<div class="fc-mobile-record"><b>{html.escape(row["vehicle_name"])}</b> · {row["end_date"]}<br>'
            f'{html.escape(t["odometer_range"])}: {values[2]}<br>{html.escape(t["distance_short"])}: {values[3]} км · '
            f'{html.escape(t["expense"])}: {values[5]} л<br>{html.escape(t["expected_short"])}: {values[8]} л</div>'
        )
    table = '<div class="fc-table-wrap"><table class="fc-table"><thead><tr>' + "".join(
        f"<th>{html.escape(x)}</th>" for x in headers
    )
    table += (
        "</tr></thead><tbody>"
        + "".join(rows)
        + '</tbody></table></div><div class="fc-mobile-records">'
        + "".join(cards)
        + "</div>"
    )
    st.markdown(table, unsafe_allow_html=True)


def vehicle_cards(vehicles):
    for vehicle in vehicles:
        status = t["active"] if vehicle["active"] else t["archived"]
        badge = "fc-badge" if vehicle["active"] else "fc-badge off"
        details = (
            " · ".join(filter(None, [vehicle["plate_number"], vehicle["fuel_type"]]))
            or "—"
        )
        st.markdown(
            f'<div class="fc-vehicle"><span class="{badge}">{html.escape(status)}</span><b>🚙 {html.escape(vehicle["name"])}</b><br>'
            f'<span class="fc-subtitle">{html.escape(details)} · {html.escape(t["summer"])}: {vehicle["summer_norm"]:g} · '
            f'{html.escape(t["winter"])}: {vehicle["winter_norm"]:g}</span></div>',
            unsafe_allow_html=True,
        )


if page == t["new_calculation"]:
    page_heading(t["new_calculation"], t["new_calculation_note"])
    left, right = st.columns([1.03, 0.97], gap="medium")
    vehicles = db.vehicles(include_archived=False) or db.vehicles()
    vehicles_by_id = {vehicle["id"]: vehicle for vehicle in vehicles}
    form_box = left.container(border=True)
    result_box = right.container(border=True)
    with form_box:
        st.markdown(
            f'<div class="fc-card-title">🚙 {t["basic_data"]}</div>',
            unsafe_allow_html=True,
        )
        vehicle_id = st.selectbox(
            t["vehicle"],
            list(vehicles_by_id),
            format_func=lambda value: vehicles_by_id[value]["name"],
        )
        vehicle = vehicles_by_id[vehicle_id]
        d1, d2 = st.columns(2)
        start_date = d1.date_input(t["start_date"], date.today())
        end_date = d2.date_input(t["end_date"], date.today())
        o1, o2 = st.columns(2)
        start_odo = o1.text_input(t["start_odometer"], "0", key="calc_start_odo")
        end_odo = o2.text_input(t["end_odometer"], "0", key="calc_end_odo")
        f1, f2 = st.columns(2)
        start_fuel = f1.text_input(t["start_fuel"], "0", key="calc_start_fuel")
        refueled = f2.text_input(t["refueled_fuel"], "0", key="calc_refueled")
        norm_mode = st.radio(
            t["norm_unit"], [t["summer"], t["winter"], t["custom"]], horizontal=True
        )
        season = "winter" if norm_mode == t["winter"] else "summer"
        default_norm = (
            vehicle["winter_norm"] if season == "winter" else vehicle["summer_norm"]
        )
        used_norm = st.number_input(
            t["norm_unit"],
            min_value=0.0,
            value=float(default_norm),
            step=0.01,
            label_visibility="collapsed",
        )
        note = st.text_area(t["note"], height=72, key="calc_note")
        clear_col, save_col = st.columns(2)
    calculation = None
    validation_error = None
    try:
        calculation = calculate_fuel(
            start_odo, end_odo, start_fuel, refueled, used_norm
        )
        if end_date < start_date:
            validation_error = t["date_error"]
    except ValueError as error:
        validation_error = (
            t["odometer_error"]
            if "odometer" in str(error).lower()
            else t["invalid_number"]
        )
    with result_box:
        st.markdown(
            f'<div class="fc-card-title">▦ {t["calculation_result"]}</div>',
            unsafe_allow_html=True,
        )
        if validation_error:
            st.error(validation_error)
        if calculation:
            r1, r2 = st.columns(2)
            r3, r4 = st.columns(2)
            r1.markdown(
                metric_card(
                    t["distance_km"],
                    fmt(calculation.distance_km, "км"),
                    f"{end_odo} − {start_odo}",
                ),
                unsafe_allow_html=True,
            )
            r2.markdown(
                metric_card(
                    t["used_norm"], fmt(used_norm, "л/100 км"), norm_mode, "orange"
                ),
                unsafe_allow_html=True,
            )
            r3.markdown(
                metric_card(
                    t["normative_consumption"],
                    fmt(calculation.normative_consumption),
                    f"{calculation.distance_km:g} × {used_norm:g} / 100",
                    "purple",
                ),
                unsafe_allow_html=True,
            )
            r4.markdown(
                metric_card(
                    t["calculated_balance"],
                    fmt(calculation.calculated_balance),
                    f"{start_fuel} + {refueled} − {calculation.normative_consumption}",
                    "green",
                ),
                unsafe_allow_html=True,
            )
        with st.expander(f'⛽ {t["actual_optional"]}'):
            actual = st.text_input(t["actual_end_fuel"], "", key="calc_actual")
            if actual.strip() and calculation:
                try:
                    checked = calculate_fuel(
                        start_odo, end_odo, start_fuel, refueled, used_norm, actual
                    )
                    status = (
                        t["saving"]
                        if checked.difference > 0
                        else (
                            t["overspend"]
                            if checked.difference < 0
                            else t["within_norm"]
                        )
                    )
                    a1, a2 = st.columns(2)
                    a1.metric(t["difference"], fmt(checked.difference))
                    a2.metric(status, fmt(abs(checked.difference)))
                    calculation = checked
                except ValueError:
                    st.error(t["invalid_number"])
    with form_box:

        def clear_calculator():
            for key, value in (
                ("calc_start_odo", "0"),
                ("calc_end_odo", "0"),
                ("calc_start_fuel", "0"),
                ("calc_refueled", "0"),
                ("calc_actual", ""),
                ("calc_note", ""),
            ):
                st.session_state[key] = value

        clear_col.button(
            t["clear"], use_container_width=True, on_click=clear_calculator
        )
        if save_col.button(
            t["save_record"],
            type="primary",
            use_container_width=True,
            disabled=not calculation or bool(validation_error),
        ):
            db.add_record(
                vehicle_id=vehicle_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                start_odometer=float(as_decimal(start_odo)),
                end_odometer=float(as_decimal(end_odo)),
                distance_km=float(calculation.distance_km),
                start_fuel=float(as_decimal(start_fuel)),
                refueled_fuel=float(as_decimal(refueled)),
                season=season,
                used_norm=used_norm,
                normative_consumption=float(calculation.normative_consumption),
                calculated_balance=float(calculation.calculated_balance),
                actual_end_fuel=(
                    None
                    if calculation.difference is None
                    else float(as_decimal(actual))
                ),
                difference=(
                    None
                    if calculation.difference is None
                    else float(calculation.difference)
                ),
                note=note,
            )
            st.success(t["saved"])
    st.markdown(
        f'<div class="fc-card"><div class="fc-card-title">▣ {t["recent_records"]}</div>',
        unsafe_allow_html=True,
    )
    recent_records(db.records())
    st.markdown("</div>", unsafe_allow_html=True)
    vcol, guide = st.columns([1.1, 0.9])
    with vcol:
        st.markdown(
            f'<div class="fc-card-title">🚙 {t["vehicles"]}</div>',
            unsafe_allow_html=True,
        )
        vehicle_cards(db.vehicles())
    with guide:
        st.markdown(
            f'<div class="fc-card-title">💡 {t["quick_guide"]}</div>',
            unsafe_allow_html=True,
        )
        for index, line in enumerate(t["guide_steps"], 1):
            st.markdown(f"**{index}.** {line}")

elif page == t["history"]:
    page_heading(t["history"], t["history_note"])
    vehicles = db.vehicles()
    by_id = {v["id"]: v for v in vehicles}
    selected = st.selectbox(
        t["vehicle"],
        [None, *by_id],
        format_func=lambda value: t["all"] if value is None else by_id[value]["name"],
    )
    records = db.records(selected)
    recent_records(records)
    if records:
        options = {
            f'#{r["id"]} · {r["start_date"]} — {r["end_date"]} · {r["vehicle_name"]}': r[
                "id"
            ]
            for r in records
        }
        with st.expander(t["delete"]):
            label = st.selectbox(t["history"], list(options))
            if st.button(t["delete"]):
                db.delete_record(options[label])
                st.rerun()

elif page == t["vehicles"]:
    page_heading(t["vehicles"], t["vehicles_note"])
    vehicles = db.vehicles()
    by_id = {v["id"]: v for v in vehicles}
    vehicle_cards(vehicles)
    edit_id = st.selectbox(
        t["edit_vehicle"], list(by_id), format_func=lambda value: by_id[value]["name"]
    )
    current = by_id[edit_id]
    with st.form("edit_vehicle"):
        c1, c2 = st.columns(2)
        name = c1.text_input(t["name"], current["name"])
        brand = c2.text_input(t["brand"], current["brand"])
        c1, c2 = st.columns(2)
        model = c1.text_input(t["model"], current["model"])
        plate = c2.text_input(t["plate_number"], current["plate_number"])
        fuel_type = st.text_input(t["fuel_type"], current["fuel_type"])
        c1, c2 = st.columns(2)
        summer = c1.number_input(
            t["summer_norm"], 0.0, value=float(current["summer_norm"]), step=0.01
        )
        winter = c2.number_input(
            t["winter_norm"], 0.0, value=float(current["winter_norm"]), step=0.01
        )
        active = st.checkbox(t["active"], bool(current["active"]))
        if st.form_submit_button(t["update"], use_container_width=True):
            try:
                db.update_vehicle(
                    edit_id,
                    name=name.strip(),
                    brand=brand,
                    model=model,
                    plate_number=plate,
                    fuel_type=fuel_type,
                    summer_norm=summer,
                    winter_norm=winter,
                    active=int(active),
                )
                st.rerun()
            except sqlite3.IntegrityError:
                st.error(t["duplicate"])
    with st.expander(t["add_vehicle"]):
        with st.form("add_vehicle"):
            c1, c2 = st.columns(2)
            name = c1.text_input(t["name"])
            brand = c2.text_input(t["brand"])
            c1, c2 = st.columns(2)
            model = c1.text_input(t["model"])
            plate = c2.text_input(t["plate_number"])
            fuel_type = st.text_input(t["fuel_type"])
            c1, c2 = st.columns(2)
            summer = c1.number_input(t["summer_norm"], 0.0, step=0.01, key="new_summer")
            winter = c2.number_input(t["winter_norm"], 0.0, step=0.01, key="new_winter")
            if st.form_submit_button(
                t["add"], type="primary", use_container_width=True
            ):
                try:
                    db.add_vehicle(
                        name=name.strip(),
                        brand=brand,
                        model=model,
                        plate_number=plate,
                        fuel_type=fuel_type,
                        summer_norm=summer,
                        winter_norm=winter,
                        active=1,
                    )
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(t["duplicate"])

elif page == t["excel_export"]:
    page_heading(t["excel_export"], t["export_note"])
    records = db.records()
    if records:
        st.download_button(
            t["export"],
            records_to_excel(records, export_labels()),
            "fuel-control.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info(t["no_history"])
elif page == t["settings"]:
    page_heading(t["settings"], t["settings_note"])
    st.info(t["settings_help"])
else:
    page_heading(t["instruction"], t["instruction_note"])
    for index, line in enumerate(t["guide_steps"], 1):
        st.markdown(f"### {index}. {line}")
