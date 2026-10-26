"""
visualizations.py
=================
All Plotly charts used by the app. Each function takes plain data and
returns a Plotly Figure; app.py only has to display it.

Design rules used:
    * One y-axis per chart, always with a title and unit.
    * AQI category colours are the official CPCB colours and are always shown
      together with the category NAME (never colour alone).
    * CO is in a much larger range (µg/m³ in the thousands), so it is shown in
      its own chart instead of squashing the other pollutants.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from aqi_calculator import CATEGORIES, POLLUTANTS, AQIResult, get_category

# Fixed colour order for series (cities / data types). Never cycled.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                 "#e87ba4", "#008300", "#6250d6", "#e34948"]
TEXT_COLOR = "#1f2937"
MUTED_TEXT = "#6b7280"
GRID_COLOR = "#e5e7eb"


def _base_layout(fig: go.Figure, title: str, x_title: str, y_title: str,
                 height: int = 380) -> go.Figure:
    # Leave room on the right when category names are written outside the plot
    has_side_labels = any(a.xref == "paper" and (a.x or 0) > 1 for a in fig.layout.annotations)
    fig.update_layout(
        title={"text": title, "x": 0, "font": {"size": 17, "color": TEXT_COLOR}},
        height=height,
        margin={"l": 60, "r": 105 if has_side_labels else 20, "t": 60, "b": 50},
        plot_bgcolor="white", paper_bgcolor="white",
        font={"family": "Segoe UI, Arial, sans-serif", "color": TEXT_COLOR, "size": 13},
        # Legend sits at the top right, so it never overlaps the x-axis title
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.0, "xanchor": "right", "x": 1},
        hoverlabel={"bgcolor": "white", "font_size": 13},
    )
    fig.update_xaxes(title=x_title, showgrid=False, linecolor=GRID_COLOR,
                     tickfont={"color": MUTED_TEXT})
    fig.update_yaxes(title=y_title, gridcolor=GRID_COLOR, zeroline=False,
                     tickfont={"color": MUTED_TEXT})
    return fig


def _add_category_bands(fig: go.Figure, y_max: float) -> None:
    """
    Light background bands that show the AQI category ranges, with the
    category name written just outside the right edge of the chart.
    """
    for cat in CATEGORIES:
        low = max(cat["low"] - 1, 0)
        if low >= y_max:
            break
        fig.add_hrect(y0=low, y1=cat["high"], fillcolor=cat["color"],
                      opacity=0.12, line_width=0, layer="below")
        fig.add_annotation(xref="paper", x=1.01, xanchor="left", showarrow=False,
                           y=(low + min(cat["high"], y_max)) / 2, text=cat["name"],
                           font={"size": 11, "color": MUTED_TEXT})


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
def aqi_gauge(result: AQIResult) -> go.Figure:
    """Speedometer-style gauge from 0 to 500 with the six category bands."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=result.aqi,
        number={"font": {"size": 46, "color": TEXT_COLOR}},
        title={"text": f"AQI - {result.category['name']}", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 500], "tickvals": [0, 50, 100, 200, 300, 400, 500]},
            "bar": {"color": TEXT_COLOR, "thickness": 0.25},
            "steps": [{"range": [max(c["low"] - 1, 0), c["high"]], "color": c["color"]}
                      for c in CATEGORIES],
        },
    ))
    fig.update_layout(height=280, margin={"l": 30, "r": 30, "t": 60, "b": 10},
                      paper_bgcolor="white", font={"family": "Segoe UI, Arial, sans-serif"})
    return fig


# ---------------------------------------------------------------------------
# Pollutant comparison charts
# ---------------------------------------------------------------------------
def subindex_bar_chart(result: AQIResult) -> go.Figure:
    """
    Compare pollutants fairly: each bar is the pollutant's NAQI sub-index
    (no unit, 0-500), so pollutants with different units can share one axis.
    """
    names, values, colors, labels = [], [], [], []
    for code, value in result.sub_indices.items():
        if value is None:
            continue
        cat = get_category(value)
        names.append(POLLUTANTS[code]["name"])
        values.append(round(value))
        colors.append(cat["color"])
        labels.append(f"{round(value)} · {cat['name']}")

    # Horizontal bars leave room for the "value · category" labels, even in narrow columns
    fig = go.Figure(go.Bar(
        y=names, x=values, orientation="h",
        marker={"color": colors, "line": {"color": "#9ca3af", "width": 1}},
        text=labels, textposition="outside", cliponaxis=False, textfont={"size": 12},
        hovertemplate="%{y}<br>Sub-index: %{x}<extra></extra>",
    ))
    _base_layout(fig, "Which pollutant decides the AQI?",
                 "Sub-index (0-500, no unit)", "Pollutant")
    fig.update_xaxes(range=[0, max(values + [100]) * 1.45], gridcolor=GRID_COLOR)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)")
    return fig


def concentration_bar_chart(latest: dict, averages: dict) -> go.Figure:
    """Grouped bars: latest hourly value vs. the average used for the AQI (µg/m³)."""
    codes = [c for c in POLLUTANTS if c != "co"]
    names = [POLLUTANTS[c]["name"] for c in codes]

    def series(values: dict) -> list:
        return [values.get(c) if values.get(c) is not None else None for c in codes]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Latest hourly value", x=names, y=series(latest),
                         marker_color=SERIES_COLORS[0],
                         hovertemplate="%{x}: %{y:.1f} µg/m³<extra>Latest hourly</extra>"))
    fig.add_trace(go.Bar(name="Average used for AQI (24 h / 8 h)", x=names,
                         y=series(averages), marker_color=SERIES_COLORS[1],
                         hovertemplate="%{x}: %{y:.1f} µg/m³<extra>Average for AQI</extra>"))
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.05)
    _base_layout(fig, "Pollutant concentrations (CO shown separately)",
                 "Pollutant", "Concentration (µg/m³)", height=420)
    # Long legend names: put the legend under the chart so it never covers the title
    fig.update_layout(legend={"yanchor": "top", "y": -0.25, "xanchor": "left", "x": 0},
                      margin={"b": 110})
    return fig


def _add_now_marker(fig: go.Figure, now) -> None:
    """Dotted vertical line labelled 'Now' that separates past from forecast."""
    fig.add_shape(type="line", x0=now, x1=now, y0=0, y1=1, yref="paper",
                  line={"color": MUTED_TEXT, "width": 1.5, "dash": "dot"})
    fig.add_annotation(x=now, y=0, yref="paper", text=" Now", showarrow=False,
                       yanchor="bottom", xanchor="left", font={"size": 11, "color": MUTED_TEXT})


def hourly_trend_chart(hourly: pd.DataFrame, code: str,
                       forecast: pd.DataFrame | None = None) -> go.Figure:
    """Line chart of one pollutant: measured hours (solid) + forecast (dashed)."""
    info = POLLUTANTS[code]
    hover = "%{x|%d %b %H:%M} UTC<br>%{y:.1f} " + info["unit"]
    data = hourly.dropna(subset=[code])
    fig = go.Figure(go.Scatter(
        x=data["time"], y=data[code], mode="lines+markers", name="Past 24 hours",
        line={"color": SERIES_COLORS[0], "width": 2}, marker={"size": 6},
        hovertemplate=hover + "<extra>Past</extra>",
    ))
    title = f"{info['name']} - hourly concentration"
    if forecast is not None and not forecast.empty:
        future = forecast.dropna(subset=[code])
        # Start the dashed line at the last measured point so the lines join up
        joined = pd.concat([data.tail(1), future])
        fig.add_trace(go.Scatter(
            x=joined["time"], y=joined[code], mode="lines", name="Forecast (model)",
            line={"color": SERIES_COLORS[1], "width": 2, "dash": "dash"},
            hovertemplate=hover + "<extra>Forecast</extra>",
        ))
        _add_now_marker(fig, data["time"].max())
        title += " (past and forecast)"
    return _base_layout(fig, title, "Time (UTC)", f"{info['name']} ({info['unit']})")


def aqi_timeline_chart(timeline: pd.DataFrame) -> go.Figure:
    """Hour-by-hour AQI: past 24 hours (solid) and forecast (dashed)."""
    data = timeline.dropna(subset=["aqi"])
    past, future = data[~data["is_forecast"]], data[data["is_forecast"]]
    hover = "%{x|%d %b %H:%M} UTC<br>AQI %{y} · %{customdata[0]}"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=past["time"], y=past["aqi"], mode="lines+markers", name="Past 24 hours",
        line={"color": SERIES_COLORS[0], "width": 2}, marker={"size": 6},
        customdata=past[["category"]], hovertemplate=hover + "<extra>Past</extra>"))
    if not future.empty:
        joined = pd.concat([past.tail(1), future])
        fig.add_trace(go.Scatter(
            x=joined["time"], y=joined["aqi"], mode="lines", name="Forecast (estimate)",
            line={"color": SERIES_COLORS[1], "width": 2, "dash": "dash"},
            customdata=joined[["category"]], hovertemplate=hover + "<extra>Forecast</extra>"))
        if not past.empty:
            _add_now_marker(fig, past["time"].max())

    y_max = max(float(data["aqi"].max()) * 1.15, 120) if not data.empty else 120
    _add_category_bands(fig, y_max)
    _base_layout(fig, "Hourly AQI - past 24 hours and outlook", "Time (UTC)",
                 "AQI (0-500)", height=420)
    fig.update_yaxes(range=[0, min(y_max, 520)])
    return fig


# ---------------------------------------------------------------------------
# History and comparison
# ---------------------------------------------------------------------------
def aqi_history_chart(history: pd.DataFrame) -> go.Figure:
    """AQI over time, one line per city, with category bands in the background."""
    data = history.dropna(subset=["aqi"]).sort_values("observed_at")
    fig = go.Figure()
    for i, city in enumerate(sorted(data["city"].unique())[:len(SERIES_COLORS)]):
        rows = data[data["city"] == city]
        fig.add_trace(go.Scatter(
            x=rows["observed_at"], y=rows["aqi"], mode="lines+markers", name=city,
            line={"color": SERIES_COLORS[i], "width": 2}, marker={"size": 8},
            customdata=rows[["category"]],
            hovertemplate=f"<b>{city}</b><br>" + "%{x|%d %b %Y %H:%M} UTC<br>"
                          "AQI %{y} · %{customdata[0]}<extra></extra>",
        ))
    y_max = max(float(data["aqi"].max()) * 1.15, 120) if not data.empty else 120
    _add_category_bands(fig, y_max)
    _base_layout(fig, "AQI trend over time (India NAQI)", "Observation time (UTC)",
                 "AQI (0-500)", height=420)
    fig.update_yaxes(range=[0, min(y_max, 520)])
    return fig


def city_comparison_chart(rows: pd.DataFrame) -> go.Figure:
    """Bar chart comparing AQI between cities, coloured by category."""
    data = rows.sort_values("aqi", ascending=False)
    colors = [get_category(a)["color"] for a in data["aqi"]]
    fig = go.Figure(go.Bar(
        x=data["city"], y=data["aqi"],
        marker={"color": colors, "line": {"color": "#9ca3af", "width": 1}},
        text=[f"{int(a)} · {c}" for a, c in zip(data["aqi"], data["category"])],
        textposition="outside", cliponaxis=False,
        hovertemplate="%{x}<br>AQI %{y}<extra></extra>",
    ))
    y_max = max(float(data["aqi"].max()) * 1.25, 120)
    _add_category_bands(fig, y_max)
    _base_layout(fig, "City comparison - AQI (India NAQI)", "City", "AQI (0-500)")
    fig.update_yaxes(range=[0, min(y_max, 560)])
    return fig


def compare_subindex_chart(cities: list[str], sub_indices: list[dict]) -> go.Figure:
    """Grouped bars: each pollutant's sub-index for every compared city."""
    codes = list(POLLUTANTS.keys())
    names = [POLLUTANTS[c]["name"] for c in codes]
    fig = go.Figure()
    for i, (city, subs) in enumerate(zip(cities, sub_indices)):
        values = [None if subs.get(c) is None else round(subs[c]) for c in codes]
        fig.add_trace(go.Bar(name=city, x=names, y=values,
                             marker_color=SERIES_COLORS[i % len(SERIES_COLORS)],
                             hovertemplate=f"<b>{city}</b><br>" + "%{x}: %{y}<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.05)
    return _base_layout(fig, "Which pollutant is the problem in each city?",
                        "Pollutant", "Sub-index (0-500, no unit)")


def city_map(rows: pd.DataFrame) -> go.Figure:
    """Map with one marker per city, coloured by AQI category."""
    colors = [get_category(a)["color"] for a in rows["aqi"]]
    fig = go.Figure(go.Scattermap(
        lat=rows["lat"], lon=rows["lon"], mode="markers+text",
        marker={"size": 22, "color": colors},
        text=[f"{c.split(',')[0]} · {int(a)}" for c, a in zip(rows["city"], rows["aqi"])],
        textposition="top center", textfont={"size": 13, "color": TEXT_COLOR},
        customdata=rows[["category"]],
        hovertemplate="<b>%{text}</b><br>%{customdata[0]}<extra></extra>",
    ))
    span = max(rows["lat"].max() - rows["lat"].min(), rows["lon"].max() - rows["lon"].min())
    zoom = 1.5 if span > 60 else 2.8 if span > 25 else 3.8 if span > 10 else 5 if span > 3 else 7
    fig.update_layout(
        map={"style": "carto-positron", "zoom": zoom,
             "center": {"lat": float(rows["lat"].mean()), "lon": float(rows["lon"].mean())}},
        height=420, margin={"l": 0, "r": 0, "t": 0, "b": 0}, showlegend=False)
    return fig


def category_distribution_chart(history: pd.DataFrame) -> go.Figure:
    """Stacked bars: how many saved records fell in each AQI category, per city."""
    data = history.dropna(subset=["aqi", "category"])
    counts = data.groupby(["city", "category"]).size().unstack(fill_value=0)
    fig = go.Figure()
    for cat in CATEGORIES:                     # fixed, official order and colours
        if cat["name"] in counts.columns:
            fig.add_trace(go.Bar(
                y=counts.index, x=counts[cat["name"]], name=cat["name"], orientation="h",
                marker={"color": cat["color"], "line": {"color": "white", "width": 1}},
                hovertemplate="%{y}: %{x} record(s)<extra>" + cat["name"] + "</extra>"))
    fig.update_layout(barmode="stack")
    _base_layout(fig, "Records per AQI category", "Number of records", "City",
                 height=max(260, 70 * len(counts) + 120))
    fig.update_layout(legend={"traceorder": "normal"})   # Good ... Severe, left to right
    return fig


# ---------------------------------------------------------------------------
# More charts: all pollutants at once, daily heatmap, pollutant history
# ---------------------------------------------------------------------------
def all_pollutants_chart(hourly: pd.DataFrame, forecast: pd.DataFrame | None = None) -> go.Figure:
    """
    Six small charts (one per pollutant), each with its own y-axis and unit.
    Solid line = past 24 hours, dashed line = forecast.
    """
    codes = list(POLLUTANTS)
    titles = [f"{POLLUTANTS[c]['name']} ({POLLUTANTS[c]['unit']})" for c in codes]
    fig = make_subplots(rows=2, cols=3, subplot_titles=titles,
                        horizontal_spacing=0.07, vertical_spacing=0.2)
    has_forecast = forecast is not None and not forecast.empty
    for i, code in enumerate(codes):
        row, col = i // 3 + 1, i % 3 + 1
        past = hourly.dropna(subset=[code])
        hover = "%{x|%d %b %H:%M} UTC<br>%{y:.1f} " + POLLUTANTS[code]["unit"]
        fig.add_trace(go.Scatter(
            x=past["time"], y=past[code], mode="lines", name="Past 24 hours",
            line={"color": SERIES_COLORS[0], "width": 2}, legendgroup="past",
            showlegend=i == 0, hovertemplate=hover + "<extra>Past</extra>"), row=row, col=col)
        if has_forecast:
            future = pd.concat([past.tail(1), forecast.dropna(subset=[code])])
            fig.add_trace(go.Scatter(
                x=future["time"], y=future[code], mode="lines", name="Forecast (model)",
                line={"color": SERIES_COLORS[1], "width": 2, "dash": "dash"},
                legendgroup="forecast", showlegend=i == 0,
                hovertemplate=hover + "<extra>Forecast</extra>"), row=row, col=col)
    fig.update_layout(
        title={"text": "All pollutants - hourly levels" + (" and forecast" if has_forecast else ""),
               "x": 0, "font": {"size": 17, "color": TEXT_COLOR}},
        height=560, margin={"l": 50, "r": 20, "t": 90, "b": 40},
        plot_bgcolor="white", paper_bgcolor="white",
        font={"family": "Segoe UI, Arial, sans-serif", "color": TEXT_COLOR, "size": 12},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.1, "xanchor": "right", "x": 1},
        hoverlabel={"bgcolor": "white", "font_size": 13})
    fig.update_xaxes(showgrid=False, linecolor=GRID_COLOR, tickfont={"color": MUTED_TEXT},
                     tickformat="%H:%M")
    fig.update_yaxes(gridcolor=GRID_COLOR, zeroline=False, tickfont={"color": MUTED_TEXT},
                     rangemode="tozero")
    return fig


def _category_colorscale() -> list:
    """Stepped colour scale for 0-500 that uses the six official CPCB colours."""
    scale = []
    for cat in CATEGORIES:
        low = max(cat["low"] - 1, 0) / 500
        scale += [[low, cat["color"]], [cat["high"] / 500, cat["color"]]]
    return scale


def daily_aqi_heatmap(history: pd.DataFrame) -> go.Figure:
    """Grid of cities x days; each cell is that day's average AQI in its category colour."""
    data = history.dropna(subset=["aqi"]).copy()
    data["day"] = data["observed_at"].dt.strftime("%d %b")
    data["day_sort"] = data["observed_at"].dt.date
    daily = data.groupby(["city", "day_sort", "day"], as_index=False)["aqi"].mean()
    days = daily.sort_values("day_sort")["day"].unique().tolist()
    grid = daily.pivot(index="city", columns="day", values="aqi").reindex(columns=days)

    text = grid.map(lambda v: "" if pd.isna(v) else f"{v:.0f}")
    names = grid.map(lambda v: "No data" if pd.isna(v) else get_category(v)["name"])
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=days, y=grid.index, zmin=0, zmax=500,
        colorscale=_category_colorscale(), xgap=3, ygap=3,
        text=text.values, texttemplate="%{text}", textfont={"size": 12},
        customdata=names.values,
        hovertemplate="%{y} · %{x}<br>Average AQI %{z:.0f} · %{customdata}<extra></extra>",
        colorbar={"title": "AQI", "tickvals": [25, 75, 150, 250, 350, 450],
                  "ticktext": [c["name"] for c in CATEGORIES], "len": 0.9},
    ))
    _base_layout(fig, "Daily average AQI per city", "Day (UTC)", "City",
                 height=max(280, 60 * len(grid) + 150))
    fig.update_xaxes(type="category")
    return fig


def pollutant_history_chart(history: pd.DataFrame, code: str) -> go.Figure:
    """One pollutant's saved averages over time, one line per city."""
    info = POLLUTANTS[code]
    data = history.dropna(subset=[code]).sort_values("observed_at")
    fig = go.Figure()
    for i, city in enumerate(sorted(data["city"].unique())[:len(SERIES_COLORS)]):
        rows = data[data["city"] == city]
        fig.add_trace(go.Scatter(
            x=rows["observed_at"], y=rows[code], mode="lines+markers", name=city,
            line={"color": SERIES_COLORS[i], "width": 2}, marker={"size": 7},
            hovertemplate=f"<b>{city}</b><br>" + "%{x|%d %b %Y %H:%M} UTC<br>%{y:.1f} "
                          + info["unit"] + "<extra></extra>"))
    period = f"{info['averaging_hours']} h average"
    return _base_layout(fig, f"{info['name']} over time ({period})",
                        "Observation time (UTC)", f"{info['name']} ({info['unit']})", height=400)
