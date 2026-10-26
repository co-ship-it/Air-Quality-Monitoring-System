"""
Outlook page: hourly AQI for the past 24 hours and the next 24 hours, and the
cleanest hours for outdoor activity.

The forecast comes from the provider's model (for sample data it is generated).
The forecast AQI uses the same NAQI rules (rolling 24 h / 8 h averages), so it is
an ESTIMATE and is always labelled that way.
"""

import streamlit as st

import ui
import visualizations as viz
from aqi_calculator import POLLUTANTS

st.title("24-hour outlook", icon=":material/trending_up:")
ui.city_search("outlook")
report = ui.require_report()
reading, result, timeline = report["reading"], report["result"], report["timeline"]

ui.data_banner(reading)
st.subheader(reading.display_name, icon=":material/location_on:")

if not result.is_valid:
    st.warning(result.message, icon=":material/warning:", title="AQI not available")
    st.stop()

forecast = timeline[timeline["is_forecast"]].dropna(subset=["aqi"]).head(24)
if forecast.empty:
    st.info("This data source did not provide a forecast for this city. "
            "The chart shows the last 24 hours only.", icon=":material/info:")
else:
    last = forecast.iloc[-1]
    change = int(last["aqi"]) - result.aqi
    if change <= -10:
        trend, icon = "Improving", ":material/trending_down:"
    elif change >= 10:
        trend, icon = "Getting worse", ":material/trending_up:"
    else:
        trend, icon = "Stable", ":material/trending_flat:"
    peak = forecast.loc[forecast["aqi"].idxmax()]
    low = forecast.loc[forecast["aqi"].idxmin()]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AQI now", result.aqi, border=True, height="stretch", help=result.category["name"])
    c2.metric("Outlook", trend, delta=change, delta_color="inverse",
              delta_description="in 24 h", border=True, height="stretch",
              help="Change between the AQI now and the forecast AQI 24 hours later.")
    c3.metric("Highest expected", int(peak["aqi"]), border=True, height="stretch",
              help=f"{peak['category']} at {ui.fmt_local(peak['time'])} local time")
    c4.metric("Lowest expected", int(low["aqi"]), border=True, height="stretch",
              help=f"{low['category']} at {ui.fmt_local(low['time'])} local time")
    st.caption(f"{icon} Highest around "
               f"{ui.fmt_local(peak['time'])} ({peak['category']}); lowest around "
               f"{ui.fmt_local(low['time'])} ({low['category']}) - local time.")

with st.container(border=True):
    st.plotly_chart(viz.aqi_timeline_chart(timeline), config={"displaylogo": False},
                    alt="Hourly AQI for the past 24 hours and the forecast")
    st.caption("Each point is the NAQI calculated at that hour (24 h / 8 h rolling averages). "
               "Dashed = estimate that uses the provider's model forecast.")

# --- Best hours for outdoor activity -------------------------------------------
st.subheader("Best hours to go outside", icon=":material/directions_walk:")
dominant = result.dominant_pollutant
if reading.has_forecast and dominant in reading.forecast.columns:
    upcoming = reading.forecast.dropna(subset=[dominant]).head(24)
    if not upcoming.empty:
        best = upcoming.nsmallest(3, dominant).sort_values("time")
        worst = upcoming.nlargest(3, dominant).sort_values("time")
        info = POLLUTANTS[dominant]
        good, bad = st.columns(2, border=True)
        good.markdown("**:material/check_circle: Cleanest hours (next 24 h)**")
        for _, row in best.iterrows():
            good.markdown(f"- {ui.fmt_local(row['time'])} - {info['name']} "
                          f"{row[dominant]:.0f} {info['unit']}")
        bad.markdown("**:material/cancel: Most polluted hours (next 24 h)**")
        for _, row in worst.iterrows():
            bad.markdown(f"- {ui.fmt_local(row['time'])} - {info['name']} "
                         f"{row[dominant]:.0f} {info['unit']}")
        st.caption(f"Based on the forecast hourly level of the main pollutant "
                   f"({info['name']}). Hourly values help with timing only; the official "
                   "AQI uses 24 h / 8 h averages.")
else:
    st.caption("Needs forecast data from the data source.")

if not forecast.empty:
    with st.expander("Forecast table (every 3 hours)", icon=":material/table_chart:"):
        table = forecast.iloc[::3].copy()
        table["Local time"] = table["time"].map(ui.fmt_local)
        table["Main pollutant"] = table["dominant"].map(
            lambda c: POLLUTANTS[c]["name"] if c in POLLUTANTS else "-")
        st.dataframe(
            table[["Local time", "aqi", "category", "Main pollutant"]].rename(
                columns={"aqi": "Forecast AQI", "category": "Category"}),
            hide_index=True, alt="Forecast table")
