"""History page: saved records with filters, statistics, charts and CSV export."""

from datetime import date, timedelta

import streamlit as st

import database
import ui
import visualizations as viz
from aqi_calculator import POLLUTANTS

st.title("History", icon=":material/history:")
st.caption(f"Every search is saved in a local SQLite database (data/air_quality.db). "
           f"Total records: **{database.count_observations()}**")

with st.popover("Demo tools", icon=":material/science:"):
    st.write("Add 7 days of SAMPLE records for 5 cities so the charts have data to show. "
             "They are marked as sample data.")
    if st.button("Add 7 days of sample history", icon=":material/add_chart:"):
        st.toast(f"Added {ui.seed_demo_history(7)} sample records.", icon=":material/check:")
    if st.button("Delete all sample records", icon=":material/delete:"):
        st.toast(f"Deleted {database.delete_sample_observations()} sample records. "
                 "Live records were kept.", icon=":material/delete:")

cities = database.get_cities()
if not cities:
    st.info("No records yet. Search for a city on Home, or use **Demo tools** above.",
            icon=":material/database:", title="History is empty")
    st.stop()

# --- Filters -------------------------------------------------------------------
today = date.today()
with st.container(horizontal=True, vertical_alignment="bottom"):
    city = st.selectbox("City", ["All cities"] + cities)
    picked = st.date_input("Date range (UTC)", value=(today - timedelta(days=30), today),
                           max_value=today + timedelta(days=1))
    data_type = st.segmented_control("Data type", ["all", "live", "sample"], default="all",
                                     format_func=str.capitalize) or "all"

if isinstance(picked, tuple):
    start, end = (picked + (None,))[:2]
else:
    start, end = picked, None
records = database.get_observations(None if city == "All cities" else city,
                                    start, end, data_type)
if records.empty:
    st.warning("No records match these filters.", icon=":material/filter_alt_off:")
    st.stop()

# --- Summary numbers -------------------------------------------------------------
with_aqi = records.dropna(subset=["aqi"])
c1, c2, c3, c4 = st.columns(4)
c1.metric("Records", len(records), border=True)
c2.metric("Cities", records["city"].nunique(), border=True)
c3.metric("Average AQI", f"{with_aqi['aqi'].mean():.0f}" if not with_aqi.empty else "-",
          border=True)
if not with_aqi.empty:
    worst = with_aqi.loc[with_aqi["aqi"].idxmax()]
    c4.metric("Highest AQI", int(worst["aqi"]), border=True,
              help=f"{worst['city']} on {worst['observed_at']:%d %b %Y}")
else:
    c4.metric("Highest AQI", "-", border=True)

if records["is_sample"].nunique() > 1:
    st.caption(":material/info: These results mix live and sample records. Choose "
               "'Live' or 'Sample' in Data type to view them separately.")

# --- Main graph (always visible) ---------------------------------------------------
with st.container(border=True):
    if len(with_aqi) >= 2:
        st.plotly_chart(viz.aqi_history_chart(with_aqi), config={"displaylogo": False},
                        alt="AQI over time per city")
    else:
        st.info("At least 2 records with an AQI are needed to draw a trend. "
                "Use **Demo tools** above to add sample history.")

# --- More views ----------------------------------------------------------------------
view = st.segmented_control(
    "More views", ["Daily heatmap", "Pollutant trend", "Categories", "City summary", "Records"],
    default="Daily heatmap", key="history_view")

if view == "Daily heatmap":
    if not with_aqi.empty:
        st.plotly_chart(viz.daily_aqi_heatmap(with_aqi), config={"displaylogo": False},
                        alt="Daily average AQI per city")
        st.caption("Each box is the average AQI of the saved records for that city and day, "
                   "in its category colour. Empty boxes mean no record that day.")
    else:
        st.info("No records with an AQI.")
elif view == "Pollutant trend":
    code = st.segmented_control("Pollutant", list(POLLUTANTS), default="pm2_5",
                                key="history_pollutant",
                                format_func=lambda c: POLLUTANTS[c]["name"]) or "pm2_5"
    if records[code].notna().sum() >= 2:
        st.plotly_chart(viz.pollutant_history_chart(records, code),
                        config={"displaylogo": False}, alt=f"{code} over time per city")
    else:
        st.info("Not enough saved values for this pollutant.")
elif view == "Records":
    table = records[["observed_at", "city", "aqi", "category", "dominant_pollutant",
                     "pm2_5", "pm10", "no2", "so2", "co", "o3", "data_source", "is_sample"]].copy()
    table["dominant_pollutant"] = table["dominant_pollutant"].map(
        lambda c: POLLUTANTS[c]["name"] if c in POLLUTANTS else "-")
    table["is_sample"] = table["is_sample"].map({1: "Sample", 0: "Live"})
    unit = "%.1f µg/m³"
    st.dataframe(table, hide_index=True, alt="Saved records", column_config={
        "observed_at": st.column_config.DatetimeColumn("Observed (UTC)", format="D MMM YYYY, HH:mm"),
        "city": "City",
        "aqi": st.column_config.ProgressColumn("AQI", min_value=0, max_value=500, format="%d"),
        "category": "Category", "dominant_pollutant": "Main pollutant",
        "pm2_5": st.column_config.NumberColumn("PM2.5", format=unit),
        "pm10": st.column_config.NumberColumn("PM10", format=unit),
        "no2": st.column_config.NumberColumn("NO₂", format=unit),
        "so2": st.column_config.NumberColumn("SO₂", format=unit),
        "co": st.column_config.NumberColumn("CO", format=unit),
        "o3": st.column_config.NumberColumn("O₃", format=unit),
        "data_source": "Source", "is_sample": "Type",
    })
    st.caption("Pollutant values are the averages used for the AQI "
               "(24 h for PM2.5, PM10, NO₂, SO₂; 8 h for CO, O₃).")
elif view == "Categories":
    if not with_aqi.empty:
        st.plotly_chart(viz.category_distribution_chart(with_aqi),
                        config={"displaylogo": False}, alt="Records per AQI category")
        st.caption("Shows how often each city had Good, Satisfactory, Moderate, Poor, "
                   "Very Poor or Severe air in the selected records.")
    else:
        st.info("No records with an AQI.")
elif view == "City summary":
    summary = (with_aqi.groupby("city")
               .agg(records=("aqi", "size"), average=("aqi", "mean"),
                    best=("aqi", "min"), worst=("aqi", "max"),
                    usual=("category", lambda s: s.mode().iloc[0]))
               .reset_index().sort_values("average"))
    st.dataframe(summary, hide_index=True, alt="Summary per city", column_config={
        "city": "City", "records": "Records",
        "average": st.column_config.ProgressColumn("Average AQI", min_value=0,
                                                   max_value=500, format="%.0f"),
        "best": "Lowest AQI", "worst": "Highest AQI", "usual": "Most common category",
    })

st.download_button("Export these records to CSV", database.to_csv_bytes(records),
                   file_name=f"air_quality_history_{today:%Y%m%d}.csv", mime="text/csv",
                   icon=":material/download:")
