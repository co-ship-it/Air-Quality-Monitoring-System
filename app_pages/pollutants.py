"""Pollutants page: all six pollutants with units, averages, sub-indices and charts."""

from datetime import timedelta

import pandas as pd
import streamlit as st

import ui
import visualizations as viz
from aqi_calculator import POLLUTANTS, get_category

st.title("Pollutant details", icon=":material/science:")
ui.city_search("pollutants")
report = ui.require_report()
reading, result = report["reading"], report["result"]

ui.data_banner(reading)
st.subheader(reading.display_name, icon=":material/location_on:")
st.caption(f"Latest data: {ui.fmt_time(reading.observed_at)} · "
           f"Coordinates: {reading.latitude:.2f}, {reading.longitude:.2f} · "
           f"Hours of data received: {len(reading.hourly)}")

# --- Latest hourly values ----------------------------------------------------
cols = st.columns(6)
for col, (code, info) in zip(cols, POLLUTANTS.items()):
    value = reading.latest.get(code)
    col.metric(info["name"], ui.fmt_value(value, 0) if value is not None else "N/A",
               border=True, help=f"{info['full_name']} - latest hourly value in {info['unit']}. "
                                 f"{info['description']}")
st.caption("Values above are the latest hourly concentrations in µg/m³. "
           "The AQI uses the averages in the table below.")

# --- Table -------------------------------------------------------------------
rows = []
for code, info in POLLUTANTS.items():
    sub = result.sub_indices.get(code)
    rows.append({
        "Pollutant": f"{info['name']} - {info['full_name']}",
        "Latest hourly": reading.latest.get(code),
        "Average for AQI": result.averages.get(code),
        "Averaging": f"{info['averaging_hours']} hours",
        "Sub-index": None if sub is None else round(sub),
        "Category": "-" if sub is None else get_category(sub)["name"],
    })
st.dataframe(
    pd.DataFrame(rows), hide_index=True, alt="Pollutant table",
    column_config={
        "Latest hourly": st.column_config.NumberColumn(format="%.1f µg/m³"),
        "Average for AQI": st.column_config.NumberColumn(format="%.1f µg/m³"),
        "Sub-index": st.column_config.ProgressColumn(
            min_value=0, max_value=500, format="%d",
            help="Pollutant's own AQI score (0-500). The highest one becomes the AQI."),
    },
)
st.caption("Empty cells mean the source did not provide the pollutant, or too few hours were "
           "available for the average required by the standard.")
if not result.is_valid:
    st.warning(result.message, icon=":material/warning:")

# --- Charts --------------------------------------------------------------------
st.subheader("Graphs", icon=":material/bar_chart:")
conc_col, sub_col = st.columns(2)
with conc_col.container(border=True):
    st.plotly_chart(viz.concentration_bar_chart(reading.latest, result.averages),
                    config={"displaylogo": False}, alt="Pollutant concentrations")
    co_avg = result.averages.get("co")
    st.caption(f"CO is much larger, so it is listed here instead: latest "
               f"{ui.fmt_value(reading.latest.get('co'))} µg/m³, 8-hour average "
               f"{ui.fmt_value(co_avg)} µg/m³ "
               f"(= {ui.fmt_value(None if co_avg is None else co_avg / 1000, 2)} mg/m³ for NAQI).")
with sub_col.container(border=True):
    if any(v is not None for v in result.sub_indices.values()):
        st.plotly_chart(viz.subindex_bar_chart(result), config={"displaylogo": False},
                        alt="Sub-index of each pollutant")
        st.caption("Sub-indices put every pollutant on the same 0-500 scale.")
    else:
        st.info("No sub-indices could be calculated.")

last_day = reading.hourly[reading.hourly["time"] > reading.observed_at - timedelta(hours=24)]
with st.container(border=True):
    st.plotly_chart(viz.all_pollutants_chart(last_day, reading.forecast),
                    config={"displaylogo": False},
                    alt="Hourly level of each pollutant, past 24 hours and forecast")
    st.caption("Each small chart has its own scale and unit. "
               "Dashed line = the provider's model forecast.")

with st.container(border=True):
    st.markdown("**Look closer at one pollutant**")
    choice = st.segmented_control(
        "Pollutant", list(POLLUTANTS), default="pm2_5", key="trend_pollutant",
        format_func=lambda c: POLLUTANTS[c]["name"]) or "pm2_5"
    if last_day[choice].notna().sum() >= 2:
        st.plotly_chart(viz.hourly_trend_chart(last_day, choice, reading.forecast),
                        config={"displaylogo": False}, alt=f"Hourly trend of {choice}")
    else:
        st.info("Not enough hourly values to draw a trend for this pollutant.")

if result.is_valid:
    with st.expander("Location map", icon=":material/map:"):
        location = pd.DataFrame([{"city": reading.display_name, "lat": reading.latitude,
                                  "lon": reading.longitude, "aqi": result.aqi,
                                  "category": result.category["name"]}])
        st.plotly_chart(viz.city_map(location), config={"displaylogo": False},
                        alt=f"Map of {reading.display_name}")

with st.expander("About these pollutants", icon=":material/menu_book:"):
    for info in POLLUTANTS.values():
        st.markdown(f"**{info['name']} ({info['full_name']})** - {info['description']}")
st.caption(f"Data source: {reading.source}")
