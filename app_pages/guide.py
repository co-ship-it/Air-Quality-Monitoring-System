"""AQI guide: categories, formula, breakpoint table and an interactive calculator."""

import html

import pandas as pd
import streamlit as st

from aqi_calculator import (AQI_STANDARD, BREAKPOINTS, CATEGORIES, POLLUTANTS,
                            calculate_aqi, calculate_sub_index, get_category)

st.title("AQI guide", icon=":material/menu_book:")
st.markdown(f"This app uses **{AQI_STANDARD}** - India's National Air Quality Index launched "
            "by the Central Pollution Control Board in 2014. It turns pollutant levels into one "
            "number from **0 to 500**. Higher means more polluted.")

# --- Categories --------------------------------------------------------------
st.subheader("AQI categories", icon=":material/palette:")
for cat in CATEGORIES:
    st.html(f"""
    <div style="display:flex;align-items:center;gap:14px;padding:8px 12px;margin-bottom:6px;
                border:1px solid #e5e7eb;border-radius:10px;background:#fff">
      <div style="min-width:150px;text-align:center;padding:6px 10px;border-radius:8px;
                  font-weight:700;background:{cat['color']};color:{cat['text_color']}">
        {cat['name']}<br><span style="font-weight:400">{cat['low']} - {cat['high']}</span></div>
      <div><b>{html.escape(cat['meaning'])}</b><br>
        <span style="color:#4b5563">{html.escape(cat['health_impact'])}</span></div>
    </div>""")

# --- Try it yourself ---------------------------------------------------------
st.subheader("Try it yourself: AQI calculator", icon=":material/calculate:")
st.caption("Enter average concentrations and see how the AQI is calculated, step by step. "
           "Untick a pollutant to treat it as missing.")
defaults = {"pm2_5": 45.0, "pm10": 175.0, "no2": 40.0, "so2": 10.0, "co": 900.0, "o3": 60.0}
with st.container(border=True):
    inputs = {}
    cols = st.columns(6)
    for col, (code, info) in zip(cols, POLLUTANTS.items()):
        with col:
            use = st.checkbox(f"Use {info['name']}", value=code in ("pm2_5", "pm10", "no2"),
                              key=f"calc_use_{code}")
            value = st.number_input(f"{info['name']} ({info['averaging_hours']} h, µg/m³)",
                                    min_value=0.0, max_value=5000.0 if code != "co" else 60000.0,
                                    value=defaults[code], step=5.0, key=f"calc_{code}",
                                    disabled=not use)
            inputs[code] = value if use else None

    calc = calculate_aqi(inputs)
    steps = []
    for code, info in POLLUTANTS.items():
        value = inputs[code]
        sub = calculate_sub_index(code, value)
        steps.append({
            "Pollutant": info["name"],
            "Average": "-" if value is None else f"{value:g} µg/m³" + (
                f" = {value / 1000:g} mg/m³" if code == "co" else ""),
            "Sub-index": None if sub is None else round(sub),
            "Category": "-" if sub is None else get_category(sub)["name"],
        })
    st.dataframe(pd.DataFrame(steps), hide_index=True, alt="Calculation steps",
                 column_config={"Sub-index": st.column_config.ProgressColumn(
                     min_value=0, max_value=500, format="%d")})
    if calc.is_valid:
        st.success(f"AQI = highest sub-index = **{calc.aqi}** → **{calc.category['name']}**, "
                   f"main pollutant **{POLLUTANTS[calc.dominant_pollutant]['name']}**.",
                   icon=":material/check_circle:", title="Result")
    else:
        st.warning(calc.message, icon=":material/warning:", title="AQI cannot be reported")

# --- Method ------------------------------------------------------------------
st.subheader("How the AQI is calculated", icon=":material/functions:")
st.markdown("""
1. **Average** each pollutant over the period set by the standard:
   24 hours for PM2.5, PM10, NO₂, SO₂ and 8 hours for CO and O₃.
   At least 16 of 24 hourly values (or 6 of 8) must be valid.
2. **Sub-index** - find the breakpoint row that contains the average and interpolate:
""")
st.latex(r"I_p = I_{low} + \frac{(C_p - C_{low})\,(I_{high} - I_{low})}{C_{high} - C_{low}}")
st.markdown("""
3. **Overall AQI = the highest sub-index.** That pollutant is the *main (dominant) pollutant*.
4. The AQI is reported **only if at least 3 pollutants** have valid data and one of them
   is **PM2.5 or PM10**. Otherwise the app says the AQI cannot be calculated.
""")

st.subheader("Breakpoint table", icon=":material/table_chart:")
labels = ["0-50", "51-100", "101-200", "201-300", "301-400", "401-500"]
table = {"AQI range": labels, "Category": [c["name"] for c in CATEGORIES]}
for code, rows in BREAKPOINTS.items():
    unit = "mg/m³" if code == "co" else "µg/m³"
    col = f"{POLLUTANTS[code]['name']} ({POLLUTANTS[code]['averaging_hours']} h, {unit})"
    table[col] = [f"{lo:g}-{hi:g}" for lo, hi, _, _ in rows[:-1]] + [f"> {rows[-1][0]:g}"]
st.dataframe(pd.DataFrame(table), hide_index=True, alt="NAQI breakpoint table")
st.caption("The official 'Severe' range has no upper limit. To keep the scale at 500, this "
           "project assumes an upper limit for the line and caps the AQI at 500.")
st.info("OpenWeatherMap uses its own 1-5 scale and the USA uses the EPA AQI with different "
        "breakpoints. This app never mixes them: every AQI shown here is calculated by our own "
        "code using the Indian NAQI.", icon=":material/info:",
        title="Not every 'index' is the same")
