"""Responsive Streamlit UI for universal odometer-based fuel accounting."""

import sqlite3
from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from fuel_control.calculations import as_decimal, calculate_fuel
from fuel_control.database import Database
from fuel_control.export import records_to_excel
from fuel_control.i18n import TEXT

st.set_page_config(page_title="Fuel Control", page_icon="⛽", layout="wide")
st.markdown("""<style>
.block-container{max-width:1050px;padding-top:1.2rem;padding-bottom:3rem}
[data-testid="stMetric"]{background:#f5f8f5;border:1px solid #dfe8df;border-radius:12px;padding:14px}
@media(max-width:640px){.block-container{padding:1rem .7rem 2rem}h1{font-size:1.6rem!important}
[data-testid="stMetric"]{padding:9px}[data-testid="stDataFrame"]{font-size:.78rem}}
</style>""", unsafe_allow_html=True)

language = st.sidebar.radio("Тіл / Язык", ["Қазақша", "Русский"], horizontal=True)
t = TEXT["kk" if language == "Қазақша" else "ru"]
db = Database()


def number(text: str) -> Decimal:
    return as_decimal(text)


def fmt(value: Decimal, unit="л") -> str:
    return f"{value:.2f} {unit}"


st.title(t["title"])
st.caption(t["subtitle"])
calculator_tab, history_tab, vehicles_tab = st.tabs([t["calculate"], t["history"], t["vehicles"]])

with calculator_tab:
    vehicles = db.vehicles(include_archived=False)
    if not vehicles:
        vehicles = db.vehicles()
    vehicles_by_id = {vehicle["id"]: vehicle for vehicle in vehicles}
    vehicle_id = st.selectbox(
        t["vehicle"], list(vehicles_by_id), format_func=lambda value: vehicles_by_id[value]["name"]
    )
    vehicle = vehicles_by_id[vehicle_id]
    dates1, dates2 = st.columns(2)
    start_date = dates1.date_input(t["start_date"], date.today())
    end_date = dates2.date_input(t["end_date"], date.today())
    season_label = st.radio(t["season"], [t["summer"], t["winter"]], horizontal=True)
    season = "summer" if season_label == t["summer"] else "winter"
    profile_norm = float(vehicle[f"{season}_norm"])
    used_norm = st.number_input(t["norm_unit"], min_value=0.0, value=profile_norm, step=0.01)

    odo1, odo2 = st.columns(2)
    start_odometer_text = odo1.text_input(t["start_odometer"], "0")
    end_odometer_text = odo2.text_input(t["end_odometer"], "0")
    fuel1, fuel2 = st.columns(2)
    start_fuel_text = fuel1.text_input(t["start_fuel"], "0")
    refueled_text = fuel2.text_input(t["refueled_fuel"], "0")
    actual_text = st.text_input(t["actual_end_fuel"], "")
    note = st.text_area(t["note"], height=70)

    calculation = None
    validation_error = None
    try:
        calculation = calculate_fuel(
            number(start_odometer_text), number(end_odometer_text), number(start_fuel_text),
            number(refueled_text), used_norm, actual_text,
        )
        if end_date < start_date:
            validation_error = t["date_error"]
    except ValueError as error:
        validation_error = t["odometer_error"] if "odometer" in str(error).lower() else t["invalid_number"]

    if validation_error:
        st.error(validation_error)
    elif calculation:
        result1, result2, result3, result4 = st.columns(4)
        result1.metric(t["distance_km"], fmt(calculation.distance_km, "км"))
        result2.metric(t["used_norm"], fmt(Decimal(str(used_norm)), "л/100 км"))
        result3.metric(t["normative_consumption"], fmt(calculation.normative_consumption))
        result4.metric(t["calculated_balance"], fmt(calculation.calculated_balance))
        if calculation.difference is not None:
            actual = number(actual_text)
            extra1, extra2, extra3 = st.columns(3)
            extra1.metric(t["actual_balance"], fmt(actual))
            extra2.metric(t["difference"], fmt(calculation.difference))
            status = t["saving"] if calculation.difference > 0 else t["overspend"] if calculation.difference < 0 else t["within_norm"]
            extra3.metric(status, fmt(abs(calculation.difference)))
        if st.button(t["save"], type="primary", use_container_width=True):
            db.add_record(
                vehicle_id=vehicle_id, start_date=start_date.isoformat(), end_date=end_date.isoformat(),
                start_odometer=float(number(start_odometer_text)), end_odometer=float(number(end_odometer_text)),
                distance_km=float(calculation.distance_km), start_fuel=float(number(start_fuel_text)),
                refueled_fuel=float(number(refueled_text)), season=season, used_norm=used_norm,
                normative_consumption=float(calculation.normative_consumption),
                calculated_balance=float(calculation.calculated_balance),
                actual_end_fuel=None if calculation.difference is None else float(number(actual_text)),
                difference=None if calculation.difference is None else float(calculation.difference), note=note,
            )
            st.success(t["saved"])

with history_tab:
    all_vehicles = db.vehicles()
    vehicles_by_id = {vehicle["id"]: vehicle for vehicle in all_vehicles}
    filter_id = st.selectbox(t["vehicle"], [None, *vehicles_by_id],
        format_func=lambda value: t["all"] if value is None else vehicles_by_id[value]["name"], key="history_vehicle")
    records = db.records(filter_id)
    if not records:
        st.info(t["no_history"])
    else:
        labels = {"vehicle_name":t["vehicle_name"], "period":t["period_export"], "start_odometer":t["start_odometer"],
          "end_odometer":t["end_odometer"], "distance_km":t["distance_km"], "used_norm":t["norm_unit"],
          "start_fuel":t["start_fuel_export"], "refueled_fuel":t["refueled_fuel_export"],
          "normative_consumption":t["normative_consumption"], "calculated_balance":t["calculated_balance"],
          "actual_end_fuel":t["actual_end_fuel_export"], "difference":t["difference"], "sheet":t["sheet"]}
        shown = pd.DataFrame([{**row, "period":f'{row["start_date"]} — {row["end_date"]}'} for row in records])
        columns = [key for key in labels if key != "sheet"]
        st.dataframe(shown[columns].rename(columns=labels), use_container_width=True, hide_index=True)
        st.download_button(t["export"], records_to_excel(records, labels), "fuel-control.xlsx",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        options = {f'#{row["id"]} · {row["start_date"]} — {row["end_date"]} · {row["vehicle_name"]}':row["id"] for row in records}
        with st.expander(t["delete"]):
            label = st.selectbox(t["history"], list(options))
            if st.button(t["delete"], use_container_width=True):
                db.delete_record(options[label])
                st.success(t["deleted"])
                st.rerun()

with vehicles_tab:
    all_vehicles = db.vehicles()
    vehicles_by_id = {vehicle["id"]: vehicle for vehicle in all_vehicles}
    edit_id = st.selectbox(t["edit_vehicle"], list(vehicles_by_id),
        format_func=lambda value: vehicles_by_id[value]["name"], key="edit_vehicle")
    current = vehicles_by_id[edit_id]
    with st.form("edit_vehicle"):
        name = st.text_input(t["name"], current["name"])
        brand = st.text_input(t["brand"], current["brand"])
        model = st.text_input(t["model"], current["model"])
        plate = st.text_input(t["plate_number"], current["plate_number"])
        fuel_type = st.text_input(t["fuel_type"], current["fuel_type"])
        c1, c2 = st.columns(2)
        summer = c1.number_input(t["summer_norm"], 0.0, value=float(current["summer_norm"]), step=0.01)
        winter = c2.number_input(t["winter_norm"], 0.0, value=float(current["winter_norm"]), step=0.01)
        active = st.checkbox(t["active"], bool(current["active"]))
        if st.form_submit_button(t["update"], use_container_width=True):
            try:
                db.update_vehicle(edit_id, name=name.strip(), brand=brand, model=model, plate_number=plate,
                    fuel_type=fuel_type, summer_norm=summer, winter_norm=winter, active=int(active))
                st.success(t["updated"])
                st.rerun()
            except sqlite3.IntegrityError:
                st.error(t["duplicate"])
    st.divider()
    st.subheader(t["add_vehicle"])
    with st.form("add_vehicle"):
        new_name = st.text_input(t["name"], key="new_name")
        new_brand = st.text_input(t["brand"], key="new_brand")
        new_model = st.text_input(t["model"], key="new_model")
        new_plate = st.text_input(t["plate_number"], key="new_plate")
        new_fuel = st.text_input(t["fuel_type"], key="new_fuel")
        n1, n2 = st.columns(2)
        new_summer = n1.number_input(t["summer_norm"], 0.0, step=0.01, key="new_summer")
        new_winter = n2.number_input(t["winter_norm"], 0.0, step=0.01, key="new_winter")
        if st.form_submit_button(t["add"], type="primary", use_container_width=True):
            if not new_name.strip():
                st.error(t["required"])
            else:
                try:
                    db.add_vehicle(name=new_name.strip(), brand=new_brand, model=new_model, plate_number=new_plate,
                        fuel_type=new_fuel, summer_norm=new_summer, winter_norm=new_winter, active=1)
                    st.success(t["added"])
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(t["duplicate"])
