"""Responsive Streamlit dashboard for odometer-based fuel accounting."""

import html
import sqlite3
from base64 import b64encode
from datetime import date
from decimal import Decimal
from pathlib import Path

import streamlit as st

from fuel_control.calculations import as_decimal, calculate_fuel
from fuel_control.database import Database
from fuel_control.export import records_to_excel
from fuel_control.i18n import TEXT

st.set_page_config(
    page_title="Fuel Control",
    page_icon="assets/logo.svg",
    layout="wide",
    initial_sidebar_state="auto",
)
st.markdown(
    """<style>
:root{--fc-blue:#0868df;--fc-navy:#102a56;--fc-border:#dbe6f2;--fc-bg:#f5f8fc}
.stApp{background:linear-gradient(135deg,#f7faff 0%,#fff 52%,#f4f8fd 100%);color:var(--fc-navy)}
.block-container{max-width:1320px;padding:3.75rem 1.5rem 3rem}.fc-brand{font-size:1.48rem;font-weight:800;color:#0b2348}
.fc-banner{height:250px;border:1px solid var(--fc-border);border-radius:16px;background-size:cover;background-position:center 62%;position:relative;overflow:hidden;box-shadow:0 10px 30px rgba(15,45,92,.14)}
.fc-banner-copy{position:absolute;inset:0;display:flex;align-items:flex-start;padding:1.35rem 1.5rem;background:linear-gradient(90deg,rgba(5,28,59,.78) 0%,rgba(5,28,59,.48) 34%,rgba(5,28,59,.08) 67%,rgba(5,28,59,.18) 100%)}
.fc-banner .fc-brand{color:#fff;text-shadow:0 1px 6px rgba(0,0,0,.3)}.fc-banner .fc-subtitle{color:#e7f2ff}.fc-logo{width:48px;height:48px;margin-right:.8rem}.fc-slogan{position:absolute;left:34%;top:22%;font-size:1.15rem;font-style:italic;color:#fff;text-shadow:0 2px 8px rgba(0,0,0,.65)}
.fc-icon{display:inline-block;width:1.35rem;height:1.35rem;vertical-align:-.3rem;margin-right:.45rem;color:#1677ff}.fc-info{margin-top:1rem;padding:.7rem .8rem;background:#f5f9ff;border-top:1px solid var(--fc-border);color:#60738f;font-size:.82rem}
.fc-subtitle{color:#60738f;font-size:.88rem}.fc-page-title{font-size:1.75rem;font-weight:800;margin:.8rem 0 .05rem}
.fc-page-note{color:#60738f;margin-bottom:1.1rem}.fc-card{background:#fff;border:1px solid var(--fc-border);border-radius:12px;
padding:1.15rem;box-shadow:0 2px 10px rgba(34,75,120,.035);margin-bottom:1rem}.fc-card-title{font-size:1.05rem;font-weight:750;margin-bottom:.9rem}
.fc-result{min-height:122px;border-radius:11px;padding:1rem;background:#edf7ff;color:#155ea8}.fc-result.orange{background:#fff3e6;color:#9d4a00}
.fc-result.purple{background:#f4efff;color:#5833b8}.fc-result.green{background:#eafaf1;color:#087240}.fc-result.red{background:#fff0f0;color:#b42318}.fc-label{font-size:.82rem;font-weight:650}
.fc-value{font-size:1.65rem;font-weight:800;margin:.3rem 0}.fc-formula{font-size:.78rem;opacity:.72}.fc-status{border-radius:10px;padding:.9rem;background:#f6f9fd;text-align:center}
.fc-vehicle{border:1px solid var(--fc-border);border-radius:10px;padding:.8rem;margin:.5rem 0;background:#fff}.fc-vehicle b{font-size:.98rem}
.fc-badge{float:right;background:#daf6e3;color:#08733b;border-radius:999px;padding:.18rem .55rem;font-size:.72rem}.fc-badge.off{background:#edf0f4;color:#667085}
.fc-table-wrap{overflow-x:auto}.fc-table{width:100%;border-collapse:collapse;font-size:.78rem}.fc-table th{background:#eaf0f7;color:#435673;text-align:left}
.fc-table th,.fc-table td{padding:.55rem;border:1px solid #dce5ef;white-space:nowrap}.fc-mobile-records{display:none}.fc-mobile-record{background:#fff;border:1px solid var(--fc-border);border-radius:10px;padding:.8rem;margin:.55rem 0}
section[data-testid="stSidebar"]{background:#f7faff;border-right:1px solid var(--fc-border)}
section[data-testid="stSidebar"] [role="radiogroup"] label{padding:.48rem .6rem;border-radius:8px;margin:.15rem 0}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:#1677ff;color:#fff}
.fc-sidebar-brand{text-align:left;color:#416183;padding:.2rem 1rem 1rem;font-size:.88rem}.fc-sidebar-road{width:100%;margin-top:8rem}
div[data-testid="stButton"] button,div[data-testid="stDownloadButton"] button{border-radius:8px;min-height:2.65rem;font-weight:650}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,textarea{border-radius:8px!important}
@media(max-width:700px){.block-container{padding:calc(3.75rem + env(safe-area-inset-top, 0px)) .65rem 2rem}.fc-brand{font-size:1.15rem}.fc-page-title{font-size:1.45rem}
.fc-banner{height:150px;background-position:center 62%}.fc-banner-copy{padding:.75rem;background:linear-gradient(90deg,rgba(5,28,59,.78),rgba(5,28,59,.35) 65%,transparent)}.fc-logo{width:34px;height:34px}.fc-slogan{display:none}
.fc-result{min-height:104px;padding:.75rem}.fc-value{font-size:1.3rem}.fc-table-wrap{display:none}.fc-mobile-records{display:block}
div[data-testid="stHorizontalBlock"]{gap:.55rem}.fc-card{padding:.8rem}.fc-vehicle .fc-badge{float:none;display:inline-block;margin-top:.35rem}}
</style>""",
    unsafe_allow_html=True,
)

db = Database()


def asset_data(path: str) -> str:
    return b64encode(Path(path).read_bytes()).decode("ascii")


header, switch, profile = st.columns([5, 1.05, 0.3], vertical_alignment="center")
language = switch.radio(
    "Language", ["Қаз", "Рус"], horizontal=True, label_visibility="collapsed"
)
t = TEXT["kk" if language == "Қаз" else "ru"]
profile.markdown(
    '<svg aria-label="Profile" viewBox="0 0 24 24" width="30" height="30" fill="none" stroke="#315679" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="9" r="3"/><path d="M6.5 19c.8-3 2.7-4.5 5.5-4.5s4.7 1.5 5.5 4.5"/></svg>',
    unsafe_allow_html=True,
)
header.markdown(
    f'<div class="fc-banner" style="background-image:url(data:image/png;base64,{asset_data("assets/hero_banner.png")})">'
    f'<div class="fc-banner-copy"><img class="fc-logo" src="data:image/svg+xml;base64,{asset_data("assets/logo.svg")}">'
    f'<div><div class="fc-brand">Fuel Control</div><div class="fc-subtitle">{t["brand_subtitle"]}</div></div></div>'
    f'<div class="fc-slogan">{html.escape(t["header_slogan"])}</div></div>',
    unsafe_allow_html=True,
)

menu_labels = [
    f'⊕  {t["new_calculation"]}',
    f'◷  {t["history"]}',
    f'▱  {t["vehicles"]}',
    f'⇩  {t["excel_export"]}',
    f'◇  {t["settings"]}',
    f'?  {t["instruction"]}',
]
page = st.sidebar.radio(
    "Fuel Control", menu_labels, label_visibility="collapsed", key="navigation"
)
page_key = ("new", "history", "vehicles", "export", "settings", "instruction")[
    menu_labels.index(page)
]
st.sidebar.caption("v1.1.0")
st.sidebar.markdown(
    f'<img class="fc-sidebar-road" src="data:image/svg+xml;base64,{asset_data("assets/sidebar-road.svg")}">'
    f'<div class="fc-sidebar-brand"><b>{t["sidebar_slogan_1"]}</b><br>{t["sidebar_slogan_2"]}</div>',
    unsafe_allow_html=True,
)


def fmt(value: Decimal | float, unit="л") -> str:
    return f"{Decimal(str(value)):.2f} {unit}"


ICONS = {
    "car": '<path d="M4 16l2-6h12l2 6M3 16h18v4h-2v-2H5v2H3v-4Zm4-6 2-4h6l2 4M7 15h.01M17 15h.01"/>',
    "chart": '<path d="M4 20V10m6 10V4m6 16v-7m4 7H2"/>',
    "road": '<path d="M8 22 10 2m6 20L14 2M12 6v3m0 4v3m0 4v2"/>',
    "gauge": '<path d="M4 18a8 8 0 1 1 16 0M12 18l4-6M6 18h12"/>',
    "fuel": '<path d="M5 21V4h10v17M4 21h12M7 8h6v5H7m8-6h2l3 3v8a2 2 0 0 1-4 0v-5"/>',
    "tank": '<path d="M4 8h16v12H4zM7 8V5h10v3M8 14h8"/>',
    "history": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5m4-1v5l3 2"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.8 9a2.3 2.3 0 1 1 3.4 2c-1.2.7-1.2 1.2-1.2 2m0 4h.01"/>',
}


def icon(name: str) -> str:
    return f'<svg class="fc-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>'


def metric_card(label, value, formula, color="", icon_name="chart"):
    return f'<div class="fc-result {color}">{icon(icon_name)}<span class="fc-label">{html.escape(label)}</span><div class="fc-value">{html.escape(value)}</div><div class="fc-formula">{html.escape(formula)}</div></div>'


def page_heading(title, note):
    st.markdown(
        f'<div class="fc-page-title">{icon("fuel")}{html.escape(title)}</div><div class="fc-page-note">{html.escape(note)}</div>',
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
            f'<div class="fc-vehicle"><span class="{badge}">{html.escape(status)}</span><b>{icon("car")}{html.escape(vehicle["name"])}</b><br>'
            f'<span class="fc-subtitle">{html.escape(details)} · {html.escape(t["summer"])}: {vehicle["summer_norm"]:g} · '
            f'{html.escape(t["winter"])}: {vehicle["winter_norm"]:g}</span></div>',
            unsafe_allow_html=True,
        )


if page_key == "new":
    page_heading(t["new_calculation"], t["new_calculation_note"])
    left, right = st.columns([1.03, 0.97], gap="medium")
    vehicles = db.vehicles(include_archived=False) or db.vehicles()
    vehicles_by_id = {vehicle["id"]: vehicle for vehicle in vehicles}
    form_box = left.container(border=True)
    result_box = right.container(border=True)
    with form_box:
        st.markdown(
            f'<div class="fc-card-title">{icon("car")}{t["basic_data"]}</div>',
            unsafe_allow_html=True,
        )
        select_col, manage_col = st.columns([3, 1.15], vertical_alignment="bottom")
        vehicle_id = select_col.selectbox(
            t["vehicle"],
            list(vehicles_by_id),
            format_func=lambda value: f'{vehicles_by_id[value]["name"]} ({vehicles_by_id[value]["plate_number"] or "—"})',
        )
        manage_col.button(
            t["manage_vehicles"],
            use_container_width=True,
            on_click=lambda: st.session_state.update(navigation=menu_labels[2]),
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
        summer_option = f'{t["summer"]} ({vehicle["summer_norm"]:g})'
        winter_option = f'{t["winter"]} ({vehicle["winter_norm"]:g})'
        norm_mode = st.radio(
            t["used_norm"], [summer_option, winter_option, t["custom"]], horizontal=True
        )
        season = "winter" if norm_mode == winter_option else "summer"
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
            f'<div class="fc-card-title">{icon("chart")}{t["calculation_result"]}</div>',
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
                    icon_name="road",
                ),
                unsafe_allow_html=True,
            )
            r2.markdown(
                metric_card(
                    t["used_norm"],
                    fmt(used_norm, "л/100 км"),
                    norm_mode,
                    "orange",
                    "gauge",
                ),
                unsafe_allow_html=True,
            )
            r3.markdown(
                metric_card(
                    t["normative_consumption"],
                    fmt(calculation.normative_consumption),
                    f"{calculation.distance_km:g} × {used_norm:g} / 100",
                    "purple",
                    "fuel",
                ),
                unsafe_allow_html=True,
            )
            r4.markdown(
                metric_card(
                    t["calculated_balance"],
                    fmt(calculation.calculated_balance),
                    f"{start_fuel} + {refueled} − {calculation.normative_consumption}",
                    "green",
                    "tank",
                ),
                unsafe_allow_html=True,
            )
        with st.expander(t["actual_optional"]):
            actual = st.text_input(
                t["actual_end_fuel"],
                "",
                key="calc_actual",
                placeholder=t["actual_placeholder"],
            )
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
                    status_color = (
                        "green"
                        if checked.difference > 0
                        else "red" if checked.difference < 0 else ""
                    )
                    a1.markdown(
                        metric_card(
                            t["difference"],
                            fmt(checked.difference),
                            "",
                            icon_name="chart",
                        ),
                        unsafe_allow_html=True,
                    )
                    a2.markdown(
                        metric_card(t["result"], status, "", status_color, "gauge"),
                        unsafe_allow_html=True,
                    )
                    calculation = checked
                except ValueError:
                    st.error(t["invalid_number"])
        st.markdown(
            f'<div class="fc-info">ⓘ {t["automatic_info"]}</div>',
            unsafe_allow_html=True,
        )
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
        f'<div class="fc-card"><div class="fc-card-title">{icon("history")}{t["recent_records"]}</div>',
        unsafe_allow_html=True,
    )
    recent_records(db.records())
    st.markdown("</div>", unsafe_allow_html=True)
    vcol, guide = st.columns([1.1, 0.9])
    with vcol:
        st.markdown(
            f'<div class="fc-card-title">{icon("car")}{t["vehicles"]}</div>',
            unsafe_allow_html=True,
        )
        vehicle_cards(db.vehicles())
    with guide:
        st.markdown(
            f'<div class="fc-card-title">{icon("help")}{t["quick_guide"]}</div>',
            unsafe_allow_html=True,
        )
        for index, line in enumerate(t["guide_steps"], 1):
            st.markdown(f"**{index}.** {line}")

elif page_key == "history":
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

elif page_key == "vehicles":
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

elif page_key == "export":
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
elif page_key == "settings":
    page_heading(t["settings"], t["settings_note"])
    st.info(t["settings_help"])
else:
    page_heading(t["instruction"], t["instruction_note"])
    for index, line in enumerate(t["guide_steps"], 1):
        st.markdown(f"### {index}. {line}")
