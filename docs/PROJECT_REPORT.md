# Air Quality Monitoring System Using Python

### College Project Report

| | |
|---|---|
| **Project title** | Air Quality Monitoring System Using Python |
| **Submitted by** | _[Your name, roll number]_ |
| **Course / Semester** | _[e.g. B.Tech CSE, 7th Semester]_ |
| **Guide** | _[Guide's name]_ |
| **Institution** | _[College name]_ |
| **Academic year** | _[2026–27]_ |

---

## 1. Project Title

**Air Quality Monitoring System Using Python** – a web dashboard that fetches air-pollution
data for any city, calculates the Indian National Air Quality Index (NAQI), visualises
pollutant levels, stores the history in a database and gives general health advice.

---

## 2. Abstract

Air pollution is one of the largest environmental health risks in India. Pollutant readings
such as "PM2.5 = 102 µg/m³" are hard for ordinary people to understand. This project
develops a Python application that converts raw pollutant concentrations into a single,
easy-to-understand **Air Quality Index** using the **National Air Quality Index published by
the Central Pollution Control Board (CPCB), India**.

The system obtains hourly concentrations of PM2.5, PM10, NO₂, SO₂, CO and O₃ for a city from
the Open-Meteo Air Quality API (no key required) or the OpenWeatherMap Air Pollution API
(key stored in an environment variable). A built-in, clearly labelled sample-data mode allows
offline demonstration. The application computes 24-hour and 8-hour averages as required by
the standard, calculates sub-indices by linear interpolation, reports the AQI only when the
CPCB minimum-data rules are satisfied, and classifies it into six colour-coded categories with
general health recommendations. Observations are stored in an SQLite database, can be
filtered by city, date and data type, exported to CSV, and plotted as trends. Multiple cities
can be compared when their values use the same standard and data source.

Advanced features include an hour-by-hour AQI timeline with a 24-hour outlook based on the
provider's model forecast, the best hours for outdoor activity, personalised advice and an
activity guide for six health profiles, user-defined AQI alerts, maps, a downloadable report
and an interactive AQI calculator that shows each step of the formula.

The user interface is built with Streamlit and Plotly; data processing uses Pandas and NumPy.
The project is covered by 80 automated tests (pytest), all of which pass.

**Keywords:** Air Quality Index, NAQI, CPCB, PM2.5, Python, Streamlit, SQLite, Plotly, API.

---

## 3. Introduction

Clean air is essential for health. The World Health Organization (WHO) estimates that air
pollution causes millions of premature deaths worldwide every year, and many Indian cities
regularly record "Poor" to "Severe" air quality, especially in winter.

Air quality is described by the concentrations of several pollutants, each measured in a
different unit and over a different averaging period. To make this understandable, countries
publish an **Air Quality Index**: a single number with a colour and a category name. India
launched its **National Air Quality Index (NAQI)** in 2014 with six categories – Good,
Satisfactory, Moderate, Poor, Very Poor and Severe.

This project builds a software tool that applies the NAQI method to data from public
air-quality APIs and presents the result in an attractive, interactive dashboard, so that a
student, citizen or teacher can check the air in any city within seconds.

---

## 4. Problem Statement

1. Raw pollutant data (µg/m³, mg/m³, different averaging periods) is difficult for the public
   to interpret.
2. Many websites show an "AQI" without saying which standard it uses; values from different
   standards (US EPA, India NAQI, provider-specific scales) are often confused.
3. Most free sources show only the current value and do not keep a personal history for
   later analysis or comparison.
4. Live demonstrations of internet-based projects often fail because of network problems.

**Goal:** build a simple, reliable Python application that converts pollutant data into the
Indian NAQI correctly, explains what it means for health, stores the history, compares cities,
and can also run offline using clearly labelled sample data.

---

## 5. Objectives

1. Fetch hourly air-pollution data for a user-selected city from a public API.
2. Display PM2.5, PM10, NO₂, SO₂, CO and O₃ with units and data-source information.
3. Calculate the AQI using one clearly identified standard (India NAQI, CPCB) only when the
   available data satisfy that standard's averaging and minimum-pollutant rules.
4. Classify air quality into colour-coded categories and display general health advice.
5. Visualise pollutant levels, hourly trends, historical AQI trends and city comparisons.
6. Store observations in SQLite with filtering and CSV export.
7. Handle invalid input, network failures and missing data gracefully.
8. Keep API keys secure using environment variables.
9. Provide an offline sample-data mode for demonstration.
10. Show an hourly AQI timeline and a clearly labelled 24-hour outlook (forecast estimate).
11. Personalise health advice for sensitive groups and alert the user above a chosen AQI.

---

## 6. Scope of the Project

**In scope**

- Any city that the geocoding services can find (worldwide).
- Six pollutants: PM2.5, PM10, NO₂, SO₂, CO, O₃.
- India NAQI calculation, categories and CPCB health-impact statements.
- Local, single-user desktop/laptop use through a web browser.
- History stored locally in SQLite, exported as CSV.

**Out of scope**

- Physical sensors / IoT hardware (data comes from APIs).
- Official regulatory reporting (API data are model estimates, not CPCB station readings).
- Forecasting of future AQI, user accounts, mobile apps, notifications.
- NH₃ and lead (Pb), which are part of NAQI but not provided by all sources.

---

## 7. Hardware and Software Requirements

### Hardware (minimum)

| Component | Requirement |
|---|---|
| Processor | Intel Core i3 / AMD Ryzen 3 or better |
| RAM | 4 GB (8 GB recommended) |
| Storage | 1 GB free (libraries ≈ 400 MB) |
| Network | Internet connection for live mode (not needed for sample mode) |
| Display | 1366 × 768 or higher |

### Software

| Software | Version used / required |
|---|---|
| Operating system | Windows 10/11 (also runs on Linux/macOS) |
| Python | 3.10 or newer (developed and tested with 3.13.5) |
| Streamlit | ≥ 1.50 (tested 1.66.1) |
| Pandas | ≥ 2.2 (tested 3.1.0) |
| NumPy | ≥ 1.26 (tested 2.5.4) |
| Plotly | ≥ 5.24 (tested 7.1.0) |
| Requests | ≥ 2.32 (tested 2.34.2) |
| python-dotenv | ≥ 1.0 (reads the `.env` file) |
| truststore | ≥ 0.10 (uses the Windows certificate store for HTTPS) |
| pytest | ≥ 8.0 (testing) |
| SQLite | built into Python (`sqlite3` module) |
| Browser | Chrome / Edge / Firefox |
| Editor | Visual Studio Code with the Python extension |

---

## 8. Technologies Used

| Technology | Role in the project | Why chosen |
|---|---|---|
| **Python** | All application logic | Easy to read, huge library ecosystem, popular for data work |
| **Streamlit** | Web user interface | Builds a web dashboard in pure Python – no HTML/JavaScript framework needed |
| **Pandas** | Tables of hourly data, averaging, filtering, CSV export | Industry standard for tabular data |
| **NumPy** | Generating realistic sample data (daily patterns, random noise) | Fast numerical arrays, reproducible random numbers |
| **Plotly** | Interactive gauge, bar and line charts | Hover tooltips, zoom, works directly in Streamlit |
| **SQLite** | Storing historical observations | Serverless, single file, built into Python |
| **Requests** | Calling the geocoding and air-quality APIs | Simple, reliable HTTP library with timeouts |
| **datetime** | Timestamps, UTC conversion, averaging windows | Built into Python |
| **python-dotenv** | Loads the API key from `.env` | Keeps secrets out of source code |
| **truststore** | HTTPS certificate verification via Windows | Prevents SSL errors on networks with HTTPS inspection |
| **pytest** | Automated tests | Simple test syntax, clear reports |

### Data sources

| Source | Data | Key | Notes |
|---|---|---|---|
| Open-Meteo Geocoding API | City → latitude/longitude | No | |
| Open-Meteo Air Quality API | Hourly PM2.5, PM10, NO₂, SO₂, CO, O₃ (µg/m³) | No | CAMS model data, ≈11–40 km grid |
| OpenWeatherMap Geocoding + Air Pollution History API | Same six pollutants (µg/m³) + own 1–5 index | Yes (free) | Optional |
| Built-in sample data | Generated hourly values for 10 cities | No | Not real measurements |

---

## 9. System Architecture

The system follows a simple **layered architecture**. The user interface never talks to the
API or database directly; it calls the service modules.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         USER (web browser)                           │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  http://localhost:8501
┌───────────────────────────────▼──────────────────────────────────────┐
│  PRESENTATION LAYER  –  Streamlit                                    │
│  app.py: sidebar (data source · health profile · alert · auto-save)  │
│          + top navigation                                            │
│  app_pages/: Home · Pollutants · Outlook · Compare · History ·       │
│              AQI guide · About        ui.py: shared page helpers     │
└──────┬────────────────────┬────────────────────┬─────────────────────┘
       │                    │                    │
┌──────▼───────┐   ┌────────▼────────┐   ┌───────▼────────┐   ┌──────────────────┐
│api_service.py│   │aqi_calculator.py│   │  database.py   │   │visualizations.py │
│ validate city│   │ 24h / 8h avgs   │   │ init / save    │   │ gauge, bars,     │
│ geocode      │   │ sub-indices     │   │ filter / read  │   │ trends, compare  │
│ past+forecast│   │ AQI + category  │   │ CSV export     │   │ map (Plotly)     │
│ error handling│  │ AQI timeline    │   │                │   │                  │
└──┬───────┬───┘   └─────────────────┘   └───────┬────────┘   └──────────────────┘
   │       │                                     │
   │  ┌────▼──────────┐  ┌──────────────────┐  ┌───────▼────────────┐
   │  │sample_data.py │  │ health_advice.py │  │ data/air_quality.db│
   │  │ (offline demo)│  │ profile tips,    │  │     (SQLite)       │
   │  └───────────────┘  │ activity guide   │  └────────────────────┘
   │                     └──────────────────┘
┌──▼────────────────────────────────────────┐
│ EXTERNAL APIs (HTTPS, 10 s timeout)       │
│  Open-Meteo Geocoding + Air Quality       │
│  OpenWeatherMap Geocoding + Air Pollution │
│  (key from .env → OPENWEATHER_API_KEY)    │
└───────────────────────────────────────────┘
```

---

## 10. Data Flow Diagram

### Level 0 (Context diagram)

```
                 city name, data source,
                 filters, comparison list
   ┌────────┐  ───────────────────────────►  ┌────────────────────────┐   coordinates     ┌──────────────┐
   │  USER  │                                │   0. AIR QUALITY       │ ────────────────► │ AIR-QUALITY  │
   │        │  ◄───────────────────────────  │   MONITORING SYSTEM    │ ◄──────────────── │ APIs         │
   └────────┘   AQI, category, advice,       └───────────┬────────────┘  hourly pollutant └──────────────┘
                charts, history, CSV file                │ ▲             data
                                                         ▼ │ records
                                                 ┌─────────────────────┐
                                                 │ D1  SQLite database │
                                                 └─────────────────────┘
```

### Level 1

```
 USER ──city name──► [1.0 Validate city name] ──invalid──► error message ──► USER
                              │ valid
                              ▼
                     [2.0 Get data]  ◄──── mode = sample ──── sample_data.py
                       │   │
                       │   └── mode = live ──► Geocoding API ──lat/lon──► Air-Quality API
                       │                                                    │
                       ◄────────────── hourly concentrations (µg/m³) ───────┘
                       ▼
             [3.0 Clean data]  remove forecast hours, negative/missing values
                       ▼
             [4.0 Compute averages]  24 h: PM2.5, PM10, NO₂, SO₂ (≥16 h)
                                     8 h: CO, O₃ (≥6 h)
                       ▼
             [5.0 Calculate AQI]  sub-index per pollutant → max → category
                       │          (needs ≥3 pollutants incl. PM2.5 or PM10)
          ┌────────────┼─────────────────────┐
          ▼            ▼                     ▼
 [6.0 Display]   [7.0 Save record] ──► D1 observations
  cards, gauge,         ▲
  advice, charts        │
          │      [8.0 History & export] ◄── filters (city, dates, type) ── USER
          ▼             │
         USER ◄── table, trend chart, CSV
                 [9.0 Compare cities] = steps 2.0–5.0 for each city
                        → check same standard & source → comparison chart ──► USER
```

---

## 11. Flowchart

```
                 ┌───────────┐
                 │   START   │
                 └─────┬─────┘
                       ▼
          ┌────────────────────────────┐
          │ Choose data source (sidebar)│
          └────────────┬───────────────┘
                       ▼
          ┌────────────────────────────┐
          │ Enter / choose city, click │
          │       "Check air"          │
          └────────────┬───────────────┘
                       ▼
               ◇ City name valid? ◇── No ──► Show "invalid name" ──┐
                       │ Yes                                        │
                       ▼                                            │
               ◇ Sample mode? ◇── Yes ──► Generate sample hourly data
                       │ No                         │               │
                       ▼                            │               │
          ┌────────────────────────┐                │               │
          │ Geocode city via API   │                │               │
          └────────────┬───────────┘                │               │
                       ▼                            │               │
               ◇ City found? ◇── No ──► "City not found" ───────────┤
                       │ Yes                        │               │
                       ▼                            │               │
          ┌────────────────────────┐                │               │
          │ Fetch hourly pollutants│                │               │
          └────────────┬───────────┘                │               │
                       ▼                            │               │
               ◇ API OK? ◇── No ──► "Connection / key error" ───────┤
                       │ Yes                        │               │
                       ▼◄───────────────────────────┘               │
          ┌────────────────────────────┐                            │
          │ Clean data, compute 24 h / │                            │
          │ 8 h averages               │                            │
          └────────────┬───────────────┘                            │
                       ▼                                            │
          ┌────────────────────────────┐                            │
          │ Sub-index for each pollutant│                           │
          └────────────┬───────────────┘                            │
                       ▼                                            │
      ◇ ≥3 pollutants AND (PM2.5 or PM10)? ◇── No ──► "AQI N/A" + values
                       │ Yes                                        │
                       ▼                                            │
          ┌────────────────────────────┐                            │
          │ AQI = max sub-index;       │                            │
          │ find category & advice     │                            │
          └────────────┬───────────────┘                            │
                       ▼                                            │
          ┌────────────────────────────┐                            │
          │ Show cards, gauge, warning,│                            │
          │ advice, charts             │                            │
          └────────────┬───────────────┘                            │
                       ▼                                            │
               ◇ Auto-save on? ◇── Yes ──► Save to SQLite (skip duplicate)
                       │ No                         │               │
                       ▼◄───────────────────────────┘◄──────────────┘
                 ┌───────────┐
                 │    END    │  (user may search again / open other pages)
                 └───────────┘
```

---

## 12. Database Design and Schema

**Database:** SQLite file `data/air_quality.db` (created automatically on first run).
**Table:** `observations` – one row = one AQI result for one city at one data time.

| Column | Type | Constraint | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique record number |
| `city` | TEXT | NOT NULL | City name returned by the source |
| `country` | TEXT | | Country name / code |
| `latitude` | REAL | | Latitude of the city |
| `longitude` | REAL | | Longitude of the city |
| `observed_at` | TEXT | NOT NULL | Time of the latest hourly data, UTC `YYYY-MM-DD HH:MM:SS` |
| `recorded_at` | TEXT | NOT NULL | Time the row was saved, UTC |
| `pm2_5` | REAL | | 24-hour average PM2.5, µg/m³ |
| `pm10` | REAL | | 24-hour average PM10, µg/m³ |
| `no2` | REAL | | 24-hour average NO₂, µg/m³ |
| `so2` | REAL | | 24-hour average SO₂, µg/m³ |
| `co` | REAL | | 8-hour average CO, µg/m³ |
| `o3` | REAL | | 8-hour average O₃, µg/m³ |
| `aqi` | INTEGER | NULL allowed | NAQI value 0–500; NULL if it could not be calculated |
| `category` | TEXT | | Good / Satisfactory / Moderate / Poor / Very Poor / Severe |
| `dominant_pollutant` | TEXT | | Code of pollutant with highest sub-index |
| `aqi_standard` | TEXT | NOT NULL | `India NAQI (CPCB)` |
| `data_source` | TEXT | NOT NULL | `sample`, `open-meteo` or `openweathermap` |
| `is_sample` | INTEGER | NOT NULL, default 0 | 1 = sample data, 0 = live data |

**Constraints and index**

- `UNIQUE (city, observed_at, data_source)` – the same observation is never stored twice
  (`INSERT OR IGNORE`).
- Index `idx_city_time (city, observed_at)` – speeds up history filtering.

**SQL used to create the table** (from `database.py`):

```sql
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT NOT NULL, country TEXT, latitude REAL, longitude REAL,
    observed_at TEXT NOT NULL, recorded_at TEXT NOT NULL,
    pm2_5 REAL, pm10 REAL, no2 REAL, so2 REAL, co REAL, o3 REAL,
    aqi INTEGER, category TEXT, dominant_pollutant TEXT,
    aqi_standard TEXT NOT NULL, data_source TEXT NOT NULL,
    is_sample INTEGER NOT NULL DEFAULT 0,
    UNIQUE (city, observed_at, data_source)
);
```

**Design decisions**

- The pollutant columns store the **averages used for the AQI**, so every row is
  self-consistent: the AQI can be recalculated from the row.
- Times are stored in **UTC** to avoid time-zone confusion; the UI shows UTC and local time.
- `aqi_standard` and `data_source` are stored so that only compatible values are compared.
- All queries use `?` placeholders (parameterised SQL) to prevent SQL injection.

---

## 13. Module Descriptions

### 13.1 `app.py`, `app_pages/` and `ui.py` – User interface
`app.py` is the entry point. It sets up the page, creates the database table, shows the
sidebar settings (data source, health profile, alert level, auto-save, "How to use" help
window) and the top navigation menu built with `st.navigation`. Each page is a short script
in `app_pages/`:

| Page file | What it shows |
|---|---|
| `home.py` | City search, colour AQI card, 24 h sparkline, gauge, warnings, personalised advice, activity guide, hourly AQI graph, pollutant graph, report download |
| `pollutants.py` | Six pollutant cards, table with sub-index bars, concentration and sub-index graphs, six-panel pollutant graph, single-pollutant trend, location map |
| `outlook.py` | Hourly AQI past 24 h + next 24 h, trend, expected peak and lowest, best hours to go outside |
| `compare.py` | 2–6 cities: cleanest vs most polluted, ranking chart, pollutant breakdown, map, ranked table |
| `history.py` | Filters, summary numbers, AQI trend graph, daily heatmap, pollutant trend, category distribution, city summary, records, CSV export, demo tools |
| `guide.py` | Categories, interactive AQI calculator, formula, breakpoint table |
| `about.py` | Project summary |

`ui.py` holds helpers shared by the pages:

| Function | Purpose |
|---|---|
| `init_state()` | Default values kept in `st.session_state` between pages |
| `load_reading(city, provider)` | Calls the API service; cached 10 min with `@st.cache_data` |
| `fetch_city(city)` | Fetch → AQI → hourly timeline → save → alerts; shows friendly errors |
| `city_search(key)` | Search form + quick-pick and recent-search buttons |
| `build_record()` | Converts a reading + AQI result into a database row |
| `aqi_card()`, `data_banner()` | Colour AQI card; SAMPLE / LIVE label |
| `report_text()` | Text report for the download button |
| `seed_demo_history(days)` | Inserts 7 days of labelled sample data for demonstrating trends |

### 13.2 `api_service.py` – Data acquisition
| Function / class | Purpose |
|---|---|
| `AirQualityReading` | Data class holding city, coordinates, past hourly table, forecast table, latest values, time, source |
| `AirQualityError`, `CityNotFoundError` | Exceptions with user-friendly messages |
| `validate_city_name()` | Trims spaces; allows only letters, spaces and `. , ' - ( )`; 2–80 chars |
| `get_api_key()` | Reads `OPENWEATHER_API_KEY` from the environment, ignores the placeholder |
| `_get_json()` | HTTP GET with 10 s timeout; converts timeout/connection/401/429 errors into safe messages that never contain the key |
| `geocode_open_meteo()`, `fetch_open_meteo()` | Open-Meteo city search; hourly data for the last 2 days and the next 2 days |
| `fetch_openweathermap()` | OpenWeatherMap geocoding, last 50 hours of history and the forecast |
| `fetch_sample()` | Sample data for one of 10 built-in cities: 48 past hours + 24 forecast hours |
| `_split_hourly()` | Cleans negative/missing values and splits rows into past (≤ now) and forecast (> now) |
| `get_air_quality(city, provider)` | Single entry point used by the app |

### 13.3 `aqi_calculator.py` – AQI logic
| Item | Purpose |
|---|---|
| `POLLUTANTS` | Name, unit, averaging period and description for each pollutant |
| `BREAKPOINTS` | CPCB NAQI breakpoint table |
| `CATEGORIES` | Six categories with CPCB colours, meaning, health impact and advice |
| `compute_averages()` | 24 h / 8 h averages; requires ≥16 of 24 or ≥6 of 8 valid hours |
| `calculate_sub_index()` | Linear interpolation; converts CO µg/m³ → mg/m³; caps at 500 |
| `calculate_aqi()` | Applies the ≥3 pollutants + PM rule; AQI = max sub-index |
| `get_category()` | Maps an AQI number to its category |
| `evaluate_air_quality()` | Averages + AQI in one call |
| `aqi_timeline()` | Rolling AQI for every hour of the last 24 h and every forecast hour |

### 13.4 `database.py` – Storage
`init_db()`, `save_observation()`, `get_observations(city, start_date, end_date, data_type)`,
`get_cities()`, `count_observations()`, `delete_sample_observations()`, `to_csv_bytes()`.

### 13.5 `visualizations.py` – Charts
`aqi_gauge()`, `subindex_bar_chart()`, `concentration_bar_chart()`, `hourly_trend_chart()`,
`aqi_timeline_chart()`, `aqi_history_chart()`, `city_comparison_chart()`,
`compare_subindex_chart()`, `city_map()`, `category_distribution_chart()`,
`all_pollutants_chart()` (six small charts, one per pollutant, each with its own scale),
`daily_aqi_heatmap()` (city × day grid in CPCB colours) and `pollutant_history_chart()`.
Every chart has a title, axis labels with
units, a legend where there is more than one series, and category names written next to
category colours.

### 13.6 `sample_data.py` – Offline demo data
Ten cities with base concentrations. `generate_hourly_data()` adds rush-hour peaks (morning
and evening), an afternoon ozone peak, a day-to-day factor and small random noise. The random
generator is seeded with the city name and date (`zlib.crc32`) so the demo is repeatable.

### 13.7 `health_advice.py` – Personalised advice
Six profiles (general public, children or older adults, asthma or lung disease, heart disease,
pregnant, outdoor worker or athlete). Each AQI category has a risk level 0–3; sensitive
profiles are advised one level more cautiously. `all_tips()` combines the CPCB advice with
the profile's tips (no repeats) and `activity_guide()` returns OK / Limit / Avoid for five
everyday activities.

---

## 14. Implementation Details

### 14.1 AQI calculation (India NAQI, CPCB)

**Step 1 – Averaging.** NAQI uses 24-hour averages for PM2.5, PM10, NO₂ and SO₂ and 8-hour
averages for CO and O₃. The app takes the window ending at the latest available hour.
CPCB requires at least 16 valid hourly values for a 24-hour average; the project applies the
same two-thirds rule (6 of 8) to 8-hour averages. If too few values exist, that pollutant is
left out.

**Step 2 – Sub-index.** For pollutant *p* with average concentration *Cp*, find the
breakpoint row (C_low, C_high, I_low, I_high) that contains *Cp* and calculate:

```
Ip = I_low + (Cp − C_low) × (I_high − I_low) / (C_high − C_low)
```

**Breakpoint table used** (µg/m³; CO in mg/m³):

| AQI | Category | PM10 24h | PM2.5 24h | NO₂ 24h | O₃ 8h | CO 8h (mg/m³) | SO₂ 24h |
|---|---|---|---|---|---|---|---|
| 0–50 | Good | 0–50 | 0–30 | 0–40 | 0–50 | 0–1.0 | 0–40 |
| 51–100 | Satisfactory | 51–100 | 31–60 | 41–80 | 51–100 | 1.1–2.0 | 41–80 |
| 101–200 | Moderate | 101–250 | 61–90 | 81–180 | 101–168 | 2.1–10 | 81–380 |
| 201–300 | Poor | 251–350 | 91–120 | 181–280 | 169–208 | 10.1–17 | 381–800 |
| 301–400 | Very Poor | 351–430 | 121–250 | 281–400 | 209–748 | 17.1–34 | 801–1600 |
| 401–500 | Severe | > 430 | > 250 | > 400 | > 748 | > 34 | > 1600 |

Two implementation notes, stated honestly:

- The official table uses integer ranges (0–30, 31–60). Real data has decimals (30.4), so the
  code joins the ranges end-to-end (0–30, 30–60, …) to leave no gaps.
- The "Severe" band has no official upper limit. To draw a line up to 500, the code assumes an
  upper limit (PM10 510, PM2.5 380, NO₂ 520, SO₂ 2400, CO 51 mg/m³, O₃ 1000) and caps the AQI at
  500. This only affects how high inside "Severe" a value appears, not the category.

**Step 3 – Overall AQI.** AQI = highest sub-index; that pollutant is the *dominant
pollutant*. The AQI is reported only when **at least three pollutants** have valid
sub-indices and **one of them is PM2.5 or PM10**; otherwise the app shows "AQI N/A" with the
reason.

**Worked example.** 24 h PM2.5 = 45 µg/m³ → row 30–60 → 50 + (45 − 30) × (100 − 50)/(60 − 30)
= **75**. PM10 = 175 µg/m³ → row 100–250 → 100 + 75 × 100/150 = **150**. NO₂ = 40 → **50**.
AQI = max(75, 150, 50) = **150 → Moderate**, dominant pollutant **PM10**. (This exact case is
an automated test.)

### 14.2 Not confusing indices
OpenWeatherMap returns its own index from 1 to 5. The app does **not** use it for the AQI; it
is shown only as a labelled note ("on OpenWeatherMap's own 1–5 scale – not the same as the
Indian NAQI"). Every AQI in the app is calculated by `aqi_calculator.py`, and the standard
name is stored with each database record. City comparison is allowed only when all results
share the same standard and data source.

### 14.3 Error handling
| Situation | Behaviour |
|---|---|
| Empty / too long / invalid characters in city | "Please enter a city name." / character rule message |
| City not found | "City 'X' was not found. Check the spelling, or try adding the country…" |
| No internet / timeout | "Could not connect… or switch to Sample data mode." / "did not respond in time" |
| Wrong API key (HTTP 401) | Explains the key problem; key never shown |
| Rate limit (HTTP 429) | "Too many requests… wait a minute" |
| Missing / negative values | Ignored during averaging |
| Too few pollutants or hours | AQI not calculated, reason shown |
| Unexpected error | Generic friendly message, app keeps running |
| Failed search | Previous city's result is cleared so it is not mistaken for the new city |

### 14.4 Security
- API key read from the environment (`.env` via python-dotenv); `.env` excluded by `.gitignore`.
- Error messages are created by the app, not copied from exceptions, so the request URL
  (which contains the key) is never displayed.
- Parameterised SQL queries; city text is escaped (`html.escape`) before being inserted into
  custom HTML.
- HTTPS with certificate verification for all API calls.

### 14.5 Performance and usability
- API results cached for 10 minutes (`st.cache_data`) – faster demos, fewer API calls.
- Duplicate observations ignored by the database's UNIQUE constraint.
- SAMPLE / LIVE banners on every result so the two can never be confused.

---

## 15. Testing and Sample Test Cases

Testing was done at two levels:

1. **Automated unit tests** with pytest – `python -m pytest -v` → **80 passed** (run on
   Python 3.13.5, Windows 11). Network calls are replaced with fake responses so the tests run
   offline and never use a real key.
2. **Integration test** – the whole Streamlit app was driven headlessly with Streamlit's
   `AppTest` tool through every page in sample mode and live (Open-Meteo) mode, with no
   exceptions; and the server was started with `streamlit run` and answered HTTP 200.

### Sample test cases

| ID | Module | Test case | Input | Expected result | Actual result |
|---|---|---|---|---|---|
| TC01 | AQI | Sub-index at category boundary | PM2.5 = 30 µg/m³ | 50 | Pass |
| TC02 | AQI | Interpolation inside a band | PM2.5 = 45 | 75 | Pass |
| TC03 | AQI | CO unit conversion | CO = 6000 µg/m³ (6 mg/m³) | 150 | Pass |
| TC04 | AQI | Above the scale | PM2.5 = 9999 | capped at 500 | Pass |
| TC05 | AQI | Invalid values | None, −5, NaN, ∞, "abc" | no sub-index (None) | Pass |
| TC06 | AQI | Category mapping | 50 / 51 / 201 / 401 | Good / Satisfactory / Poor / Severe | Pass |
| TC07 | AQI | Overall AQI = max sub-index | PM2.5 45, PM10 175, NO₂ 40 | 150, Moderate, PM10 | Pass |
| TC08 | AQI | Fewer than 3 pollutants | PM2.5, PM10 only | AQI not calculated | Pass |
| TC09 | AQI | No PM2.5/PM10 | NO₂, SO₂, O₃, CO | AQI not calculated | Pass |
| TC10 | AQI | Averaging windows | 30 h of data | O₃ uses last 8 h; PM2.5 last 24 h | Pass |
| TC11 | AQI | Too few hours | 10 hourly values | No 24 h average; 8 h average OK | Pass |
| TC12 | AQI | Missing / negative hours ignored | 5 missing, 1 negative | Average of valid hours | Pass |
| TC13 | DB | Save and read back | One record | 1 row, same values | Pass |
| TC14 | DB | Duplicate record | Same record twice | Second insert skipped | Pass |
| TC15 | DB | Filter by city and date | 3 records | Correct counts | Pass |
| TC16 | DB | Live/sample filter and delete | 1 live + 1 sample | Each filter returns 1; delete removes sample only | Pass |
| TC17 | DB | SQL injection attempt | `Delhi' OR '1'='1` | Treated as text, 0 rows | Pass |
| TC18 | DB | CSV export | One record | Header + data row | Pass |
| TC19 | API | Valid city names | `"  Delhi "`, `São Paulo`, `Pune, India` | Cleaned and accepted | Pass |
| TC20 | API | Invalid city names | `""`, `12345`, `Delhi<script>`, 81 chars | Error message | Pass |
| TC21 | API | Sample mode | `delhi` | Delhi, labelled sample, 24 hourly rows | Pass |
| TC22 | API | Open-Meteo success (mocked) | Delhi | AQI 75, forecast hours removed | Pass |
| TC23 | API | City not found (mocked) | `Nowhere` | CityNotFoundError | Pass |
| TC24 | API | No internet / timeout (mocked) | Connection error | Friendly message | Pass |
| TC25 | API | Wrong key (mocked 401) | Secret key | Message without the key | Pass |
| TC26 | API | Provider index kept separate | OWM index 4 | Our AQI 150; OWM index labelled separately | Pass |
| TC27 | UI | Live search (real API) | Delhi, Open-Meteo | LIVE banner, gauge, advice | Pass |
| TC28 | UI | Invalid city (real API) | `Xyzqwvbnm` | "not found" message, no old result | Pass |
| TC29 | UI | Compare with one bad city | Delhi, Mumbai, Chennai, NotARealCityzz | Chart for 3, warning for the bad one | Pass |
| TC30 | UI | Demo history + CSV | Add 7 days | Trend chart and CSV button shown | Pass |
| TC31 | AQI | Hourly timeline | 48 past + 24 forecast hours, PM2.5 45 | 48 hourly AQI values, 24 marked forecast, all 75 | Pass |
| TC32 | AQI | Timeline follows rising pollution | PM2.5 30 → 90 in forecast | Last AQI > first AQI | Pass |
| TC33 | Health | Sensitive profile is more cautious | Moderate, asthma profile | Risk level 2 (general: 1) | Pass |
| TC34 | Health | No repeated advice | Every category × profile | No duplicate tips | Pass |
| TC35 | UI | Alert level | Delhi AQI 314, alert at 201 | Pop-up alert shown | Pass |
| TC36 | UI | Health profile change | Profile → asthma | Advice and activity guide change | Pass |

---

## 16. Results and Screenshots

### Live results recorded during testing (Open-Meteo, 23 Oct 2026, 16:00 UTC)

| City | AQI (NAQI) | Category | Dominant pollutant | PM2.5 24 h (µg/m³) | PM10 24 h (µg/m³) |
|---|---|---|---|---|---|
| Delhi, India | 240 | Poor | PM2.5 | 102.0 | 230.2 |
| Pune, India | 116 | Moderate | O₃ (8 h avg 111.1) | 45.6 | 51.9 |
| London, United Kingdom | 50 | Good | O₃ (8 h avg 49.9) | 3.9 | 6.8 |

These values are model estimates from Open-Meteo (CAMS) and will differ when you run the app.

### Screenshots to insert

Run the app and capture these screens (Windows: **Win + Shift + S**). Insert them here
before submitting.

| Figure | Screen | How to get it |
|---|---|---|
| Fig. 1 | Home – sample mode (Delhi) | Sample data → click Delhi |
| Fig. 2 | Home – live mode with health warning and pop-up alert | Open-Meteo → Delhi |
| Fig. 3 | Pollutants – cards, table and charts | Pollutants page |
| Fig. 4 | Outlook – past 24 h + next 24 h and best hours | Outlook page |
| Fig. 5 | AQI Guide – categories and breakpoint table | AQI Guide page |
| Fig. 6 | History – filters, table and trend chart | History → Add 7 days of sample history |
| Fig. 7 | Exported CSV opened in Excel | History → Export to CSV |
| Fig. 8 | Compare – ranking chart and map | Compare → Compare → Map |
| Fig. 9 | Error message for an invalid city | Live mode → type "Xyzqwvbnm" |
| Fig. 10 | Test results | Terminal: `python -m pytest -v` |

_[Insert screenshots here]_

---

## 17. Limitations

1. Live values are **model estimates** (CAMS / OpenWeatherMap) for a grid cell, not official
   CPCB station readings, and may differ from government bulletins.
2. NH₃ and lead (Pb), part of the full NAQI, are not included.
3. The "Severe" band's upper concentration limits are assumptions (only the category is
   official above the lower limit).
4. The 8-hour minimum-data rule (6 of 8 hours) is a project choice following CPCB's
   two-thirds rule for 24-hour averages.
5. Live mode needs internet; free APIs have rate limits.
6. History is stored only on the local computer; no user accounts or cloud sync.
7. Health recommendations are general and not personalised medical advice.
8. Sample data are synthetic and must not be used to draw real conclusions.
9. The 24-hour outlook depends on the provider's model forecast and is only an estimate;
   "best hours" use hourly values of the main pollutant, not the official 24 h / 8 h AQI.

---

## 18. Future Enhancements

1. Integrate official CPCB station data (e.g. data.gov.in) and IoT sensors (ESP32 + PM sensor).
2. Add the US EPA AQI as a second, clearly separated standard.
3. Own AQI forecasting with machine learning (e.g. linear regression, LSTM) instead of the
   provider's model forecast.
4. Map of all monitoring stations in a city.
5. Email/SMS alerts when AQI crosses a chosen level.
6. Scheduled automatic data collection to build long-term history.
7. Deployment on Streamlit Community Cloud for public access.
8. Hindi and regional-language interface.
9. NH₃ and Pb support where data is available.

---

## 19. Conclusion

The Air Quality Monitoring System meets its objectives. It fetches real air-pollution data
for any city (or uses clearly labelled sample data offline), calculates the AQI using one
clearly identified standard – India's NAQI – while respecting its averaging and
minimum-pollutant rules, and presents the result through colour-coded cards, a gauge,
interactive Plotly charts and general health recommendations. Observations are stored in
SQLite and can be filtered, plotted and exported to CSV, and cities can be compared only when
their values are compatible.

The project demonstrates practical use of Python for API integration, data processing with
Pandas/NumPy, database design with SQLite, interactive visualisation and web UI development
with Streamlit, along with good practices such as modular design, error handling, secure key
management and automated testing (80 passing tests).

---

## 20. References

1. Central Pollution Control Board (CPCB), *National Air Quality Index*, Ministry of
   Environment, Forest & Climate Change, Government of India, 2014.
   <https://cpcb.nic.in/national-air-quality-index/>
2. World Health Organization, *WHO Global Air Quality Guidelines*, 2021.
   <https://www.who.int/publications/i/item/9789240034228>
3. Open-Meteo, *Air Quality API documentation*. <https://open-meteo.com/en/docs/air-quality-api>
4. Open-Meteo, *Geocoding API documentation*. <https://open-meteo.com/en/docs/geocoding-api>
5. Copernicus Atmosphere Monitoring Service (CAMS). <https://atmosphere.copernicus.eu/>
6. OpenWeatherMap, *Air Pollution API*. <https://openweathermap.org/api/air-pollution>
7. Streamlit documentation. <https://docs.streamlit.io/>
8. Pandas documentation. <https://pandas.pydata.org/docs/>
9. Plotly Python documentation. <https://plotly.com/python/>
10. Python `sqlite3` documentation. <https://docs.python.org/3/library/sqlite3.html>
11. Requests documentation. <https://requests.readthedocs.io/>
12. pytest documentation. <https://docs.pytest.org/>
