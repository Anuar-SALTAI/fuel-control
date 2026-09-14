"""Streamlit entry point for Fuel Control."""

import sqlite3
from datetime import date

import pandas as pd
import streamlit as st

from fuel_control.calculations import calculate_fuel
from fuel_control.database import Database
from fuel_control.export import records_to_excel
from fuel_control.i18n import TEXT


st.set_page_config(page_title="Fuel Control", page_icon="⛽", layout="wide")
st.markdown(
    """
    <style>
    .block-container {max-width: 1050px; padding-top: 1.5rem; padding-bottom: 3rem}
    [data-testid="stMetric"] {background:#f5f8f5;border:1px solid #dfe8df;border-radius:12px;padding:14px}
    @media (max-width: 640px) {
      .block-container {padding:1rem .75rem 2rem}
      h1 {font-size:1.65rem !important}
      div[data-testid="stHorizontalBlock"] {gap:.5rem}
      [data-testid="stMetric"] {padding:10px}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

language = st.sidebar.radio("Тіл / Язык", ["Қазақша", "Русский"], horizontal=True)
t = TEXT["kk" if language == "Қазақша" else "ru"]
db = Database()

st.title(t["title"])
st.caption(t["subtitle"])
calculate_tab, history_tab, vehicles_tab = st.tabs([t["calculate"], t["history"], t["vehicles"]])

with calculate_tab:
    vehicles = db.vehicles()
    selected = st.selectbox(t["vehicle"], vehicles, format_func=lambda row: row["name"])
    left, right = st.columns(2)
    with left:
        month = st.date_input(t["month"], value=date.today().replace(day=1))
    with right:
        season_label = st.radio(t["season"], [t["summer"], t["winter"]], horizontal=True)
    season = "summer" if season_label == t["summer"] else "winter"
    norm = float(selected[f"{season}_norm"])
    st.info(f'{t["norm"]}: **{norm:.2f}**')

    with st.form("calculation"):
        col1, col2 = st.columns(2)
        mileage = col1.number_input(t["mileage"], min_value=0.0, step=100.0)
        filled = col2.number_input(t["filled"], min_value=0.0, step=10.0)
        opening = col1.number_input(t["opening_balance"], min_value=0.0, step=1.0)
        closing = col2.number_input(t["closing_balance"], min_value=0.0, step=1.0)
        submitted = st.form_submit_button(t["save"], type="primary", use_container_width=True)
    if submitted:
        try:
            result = calculate_fuel(mileage, norm, filled, opening, closing)
            db.add_record(
                vehicle_id=selected["id"], month=month.strftime("%Y-%m"), season=season,
                norm=norm, mileage=mileage, filled=filled, opening_balance=opening,
                closing_balance=closing, normative_consumption=result.normative_consumption,
                actual_consumption=result.actual_consumption, difference=result.difference,
            )
            st.success(t["saved"])
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric(t["normative_consumption"], f"{result.normative_consumption:.2f} л")
            metric2.metric(t["actual_consumption"], f"{result.actual_consumption:.2f} л")
            label = t["saving"] if result.is_saving else t["overspend"]
            metric3.metric(label, f"{abs(result.difference):.2f} л")
        except ValueError as error:
            st.error(f'{t["invalid"]}: {error}')

with history_tab:
    vehicles = db.vehicles()
    choices = [None, *vehicles]
    filter_vehicle = st.selectbox(
        t["vehicle"], choices, format_func=lambda row: t["all"] if row is None else row["name"], key="history_vehicle"
    )
    records = db.records(None if filter_vehicle is None else filter_vehicle["id"])
    if not records:
        st.info(t["no_history"])
    else:
        labels = {key: t[key] for key in (
            "month", "vehicle_name", "season", "norm", "mileage", "filled", "opening_balance",
            "closing_balance", "normative_consumption", "actual_consumption", "difference", "sheet"
        )}
        display_columns = [key for key in labels if key != "sheet"]
        frame = pd.DataFrame([dict(row) for row in records])[display_columns]
        frame["season"] = frame["season"].map({"summer": t["summer"], "winter": t["winter"]})
        st.dataframe(frame.rename(columns=labels), use_container_width=True, hide_index=True)
        st.download_button(
            t["export"], records_to_excel(records, labels), "fuel-control.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
        )
        record_options = {f'#{row["id"]} · {row["month"]} · {row["vehicle_name"]}': row["id"] for row in records}
        with st.expander(t["delete"]):
            record_label = st.selectbox(t["history"], record_options)
            if st.button(t["delete"], type="secondary", use_container_width=True):
                db.delete_record(record_options[record_label])
                st.success(t["deleted"])
                st.rerun()

with vehicles_tab:
    vehicles = db.vehicles()
    edit_vehicle = st.selectbox(t["vehicle"], vehicles, format_func=lambda row: row["name"], key="edit_vehicle")
    with st.form("edit_vehicle_form"):
        summer_norm = st.number_input(t["summer_norm"], min_value=0.0, value=float(edit_vehicle["summer_norm"]), step=0.1)
        winter_norm = st.number_input(t["winter_norm"], min_value=0.0, value=float(edit_vehicle["winter_norm"]), step=0.1)
        if st.form_submit_button(t["update"], use_container_width=True):
            db.update_vehicle(edit_vehicle["id"], summer_norm, winter_norm)
            st.success(t["updated"])
    st.divider()
    st.subheader(t["add_vehicle"])
    with st.form("add_vehicle_form", clear_on_submit=True):
        name = st.text_input(t["name"])
        new_summer = st.number_input(t["summer_norm"], min_value=0.0, value=0.0, step=0.1, key="new_summer")
        new_winter = st.number_input(t["winter_norm"], min_value=0.0, value=0.0, step=0.1, key="new_winter")
        if st.form_submit_button(t["add"], type="primary", use_container_width=True):
            if not name.strip():
                st.error(t["invalid"])
            else:
                try:
                    db.add_vehicle(name, new_summer, new_winter)
                    st.success(t["added"])
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(t["duplicate"])
