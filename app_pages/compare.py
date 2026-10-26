"""Compare page: AQI of 2-6 cities side by side (same standard, same data source)."""

import pandas as pd
import streamlit as st

import api_service
import database
import sample_data
import ui
import visualizations as viz
from aqi_calculator import POLLUTANTS

st.title("Compare cities", icon=":material/compare_arrows:")
st.caption("Compare 2 to 6 cities. All values use the same AQI standard and the same data "
           "source, so the comparison is fair.")

provider = st.session_state.provider
with st.form("compare_form", border=False):
    with st.container(horizontal=True, vertical_alignment="bottom"):
        if provider == "sample":
            cities = st.multiselect("Cities", sample_data.list_sample_cities(),
                                    default=["Delhi", "Mumbai", "Bengaluru"], max_selections=6)
        else:
            cities = st.multiselect("Cities (pick or type any city)", ui.POPULAR_CITIES,
                                    default=["Delhi", "Mumbai", "Bengaluru"],
                                    accept_new_options=True, max_selections=6)
        submitted = st.form_submit_button("Compare", type="primary",
                                          icon=":material/compare_arrows:")

if submitted:
    if len(cities) < 2:
        st.warning("Please choose at least 2 cities.", icon=":material/edit:")
        st.stop()
    rows, problems = [], []
    progress = st.progress(0.0, text="Getting data...")
    for i, city in enumerate(cities, start=1):
        try:
            reading = ui.load_reading(city, provider)
            result = ui.analyse(reading)
            if st.session_state.auto_save:
                database.save_observation(ui.build_record(reading, result))
            if result.is_valid:
                rows.append({
                    "city": reading.display_name, "aqi": result.aqi,
                    "category": result.category["name"],
                    "dominant": POLLUTANTS[result.dominant_pollutant]["name"],
                    "pm2_5": result.averages.get("pm2_5"), "pm10": result.averages.get("pm10"),
                    "lat": reading.latitude, "lon": reading.longitude,
                    "standard": result.standard, "provider": reading.provider,
                    "sub_indices": result.sub_indices,
                    "observed": ui.fmt_time(reading.observed_at),
                })
            else:
                problems.append(f"{reading.display_name}: {result.message}")
        except api_service.AirQualityError as err:
            problems.append(f"{city}: {err}")
        except Exception:
            problems.append(f"{city}: unexpected error while getting data.")
        progress.progress(i / len(cities), text=f"Got {i} of {len(cities)} cities")
    progress.empty()
    st.session_state.compare = {"rows": rows, "problems": problems, "provider": provider}

saved = st.session_state.get("compare")
if not saved or saved["provider"] != provider:
    st.stop()

for problem in saved["problems"]:
    st.warning(problem, icon=":material/warning:", title="Skipped")
table = pd.DataFrame(saved["rows"])
if table.empty:
    st.error("No city could be compared.", icon=":material/error:")
    st.stop()

# Only compare values that use the same AQI standard AND the same data source.
if table["standard"].nunique() > 1 or table["provider"].nunique() > 1:
    st.error("These results use different standards or data sources, so they are not "
             "comparable. Please use one data source.", icon=":material/block:")
    st.stop()

if provider == "sample":
    st.warning("Demonstration values, not real measurements.", icon=":material/science:",
               title="Sample data")
else:
    st.success(api_service.PROVIDER_LABELS[provider], icon=":material/satellite_alt:",
               title="Live data")

table = table.sort_values("aqi").reset_index(drop=True)
table.insert(0, "rank", range(1, len(table) + 1))
best, worst = table.iloc[0], table.iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Cleanest air", best["city"], border=True,
          help=f"AQI {best['aqi']} · {best['category']}")
c1.caption(f"AQI {best['aqi']} · {best['category']}")
c2.metric("Most polluted", worst["city"], border=True,
          help=f"AQI {worst['aqi']} · {worst['category']}")
c2.caption(f"AQI {worst['aqi']} · {worst['category']}")
c3.metric("Difference", f"{worst['aqi'] - best['aqi']} AQI points", border=True)
c3.caption(f"Average AQI of these cities: {table['aqi'].mean():.0f}")

view = st.segmented_control("View", ["AQI ranking", "Pollutants", "Map"],
                            default="AQI ranking", key="compare_view")
if view == "AQI ranking" and len(table) >= 2:
    st.plotly_chart(viz.city_comparison_chart(table), config={"displaylogo": False},
                    alt="AQI comparison chart")
elif view == "AQI ranking":
    st.info("Only one city had a valid AQI, so a comparison chart cannot be drawn.")
elif view == "Pollutants":
    st.plotly_chart(viz.compare_subindex_chart(table["city"].tolist(),
                                               table["sub_indices"].tolist()),
                    config={"displaylogo": False}, alt="Sub-index of each pollutant per city")
    st.caption("Sub-indices put all pollutants on the same 0-500 scale; "
               "the tallest bar for each city is its main pollutant.")
elif view == "Map":
    st.plotly_chart(viz.city_map(table), config={"displaylogo": False},
                    alt="Map of compared cities coloured by AQI category")

st.dataframe(
    table[["rank", "city", "aqi", "category", "dominant", "pm2_5", "pm10", "observed"]],
    hide_index=True, alt="Comparison table",
    column_config={
        "rank": st.column_config.NumberColumn("Rank", help="1 = cleanest air"),
        "city": "City",
        "aqi": st.column_config.ProgressColumn("AQI", min_value=0, max_value=500, format="%d"),
        "category": "Category", "dominant": "Main pollutant",
        "pm2_5": st.column_config.NumberColumn("PM2.5 24 h", format="%.1f µg/m³"),
        "pm10": st.column_config.NumberColumn("PM10 24 h", format="%.1f µg/m³"),
        "observed": "Data time",
    },
)
