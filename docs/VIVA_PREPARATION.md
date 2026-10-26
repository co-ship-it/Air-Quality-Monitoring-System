# Viva Preparation – Air Quality Monitoring System Using Python

---

## 1. The whole project in simple words

> "My project is a web app made in Python. You type a city name. The app finds the city's
> location, downloads the last 24 hours of pollution readings from a free air-quality API,
> and calculates the Air Quality Index using the Indian government's formula (CPCB National
> AQI). It shows the AQI as a coloured card and a gauge, tells you which pollutant is the main
> problem, and gives simple health advice. Every result is saved in an SQLite database, so you
> can look at the history, filter it, see a trend chart and export it to Excel (CSV). You can
> also compare several cities. If there is no internet, a sample-data mode lets me demonstrate
> everything, and it is clearly labelled as sample data."

**The flow in one line:**
City name → validate → geocode (lat/lon) → hourly pollutant data → averages (24 h / 8 h) →
sub-indices → AQI = highest sub-index → category + advice → charts → saved in SQLite.

---

## 2. How each module works

| File | One-line explanation | What to say in viva |
|---|---|---|
| `app.py` | The front door | "Sets up the page, shows the sidebar settings (data source, health profile, alert level) and the navigation menu. Each page is a separate file in `app_pages/`." |
| `app_pages/` | The screens | "Seven short page scripts: Home, Pollutants, Outlook, Compare, History, AQI guide, About. They call the other modules and never talk to the API or database directly." |
| `ui.py` | Shared page helpers | "City search with quick-pick buttons, fetching a city, saving to history, alerts, the colour AQI card and the downloadable report." |
| `health_advice.py` | Personal advice | "Six health profiles. Sensitive people are advised one level more cautiously. Also gives an OK / Limit / Avoid activity guide." |
| `api_service.py` | Gets the data | "Validates the city name, converts it to latitude/longitude with a geocoding API, downloads hourly pollutant data, removes forecast and invalid values, and turns every failure into a friendly message." |
| `aqi_calculator.py` | The brain | "Calculates 24-hour and 8-hour averages, converts each to a sub-index with the CPCB breakpoint table, picks the highest as the AQI, and finds the category and health advice." |
| `database.py` | The memory | "Creates the SQLite table, saves each observation, reads records with filters for city, date and live/sample, and exports CSV." |
| `visualizations.py` | The charts | "Plotly gauge, bar charts, hourly trend, history trend and comparison chart, all with titles, units and legends." |
| `sample_data.py` | Offline demo | "Generates realistic but fake hourly values for 10 cities with rush-hour peaks. The random seed is fixed so the demo repeats." |
| `tests/` | Proof it works | "80 pytest tests check the AQI maths, hourly timeline, health advice, database and API error handling; network calls are faked." |

---

## 3. Why each technology was chosen

| Technology | Reason |
|---|---|
| **Python** | Simple syntax, best libraries for data work, taught in our course. |
| **Streamlit** | A full web dashboard written only in Python – no HTML/CSS/JavaScript framework. Widgets like text box, buttons and charts take one line each. |
| **Pandas** | Hourly data is a table; Pandas makes filtering time windows, averaging and CSV export easy. |
| **NumPy** | Used to generate the sample data – arrays, smooth daily patterns and reproducible random noise. |
| **Plotly** | Interactive charts (hover, zoom) that work inside Streamlit; has a ready-made gauge. |
| **SQLite** | No server to install, the database is one file, and `sqlite3` is built into Python. Perfect for a single-user app. |
| **Requests** | The simplest way to call a web API, with timeouts and clear errors. |
| **datetime** | To work with times in UTC, create 24 h/8 h windows and show local time. |
| **python-dotenv** | Loads the API key from a `.env` file so it is never written in code. |
| **truststore** | Makes Python trust the Windows certificate store, avoiding SSL errors on college/antivirus networks. |
| **Open-Meteo API** | Free, no key, gives all six pollutants hourly – reliable for a demo. |

---

## 4. How the AQI is calculated (learn this well)

**Standard:** India National Air Quality Index (NAQI), CPCB, 2014. Range 0–500, six categories.

1. **Average** each pollutant over the required period:
   - 24 hours: PM2.5, PM10, NO₂, SO₂ (need ≥ 16 valid hours)
   - 8 hours: CO, O₃ (need ≥ 6 valid hours)
2. **Sub-index** by linear interpolation inside the breakpoint row:

   `Ip = I_low + (Cp − C_low) × (I_high − I_low) / (C_high − C_low)`

3. **AQI = maximum sub-index**; that pollutant is the **dominant pollutant**.
4. Report only if **≥ 3 pollutants** are available **and one is PM2.5 or PM10**.

**Example to write on the board:**
PM2.5 = 45 → band 30–60 → 50 + (45 − 30) × 50 / 30 = **75**
PM10 = 175 → band 100–250 → 100 + (175 − 100) × 100 / 150 = **150**
NO₂ = 40 → **50**
AQI = max(75, 150, 50) = **150 → Moderate**, dominant = **PM10**.

| AQI | Category | Colour |
|---|---|---|
| 0–50 | Good | Dark green |
| 51–100 | Satisfactory | Light green |
| 101–200 | Moderate | Yellow |
| 201–300 | Poor | Orange |
| 301–400 | Very Poor | Red |
| 401–500 | Severe | Maroon |

**Key PM2.5 breakpoints to remember:** 30, 60, 90, 120, 250.
**Key PM10 breakpoints:** 50, 100, 250, 350, 430.

---

## 5. How data is stored in SQLite

- File: `data/air_quality.db`, table `observations`, created automatically by `init_db()`
  using `CREATE TABLE IF NOT EXISTS`.
- Each search saves: city, country, latitude, longitude, data time (UTC), save time,
  the six averaged pollutant values, AQI, category, dominant pollutant, AQI standard, data
  source and a sample/live flag.
- `UNIQUE (city, observed_at, data_source)` + `INSERT OR IGNORE` → no duplicates if you
  click twice.
- Reading uses `SELECT … WHERE city = ? AND observed_at >= ? …` – the `?` placeholders make
  it safe from SQL injection.
- `pandas.read_sql_query()` turns the result into a table for display, charting and
  `to_csv()` export.

---

## 6. Viva questions and answers

### Basics

**1. What is the Air Quality Index?**
A single number (0–500 in India) that summarises how polluted the air is, with a colour and a
category name, so the public can understand it without knowing pollutant units.

**2. Which AQI standard does your project use and why?**
India's National AQI by CPCB (2014), because the project is for Indian users, it is the
official Indian standard, and it uses µg/m³ – the same unit the APIs return – so no unit
conversion errors (except CO, which we convert to mg/m³).

**3. Which pollutants does your project monitor?**
PM2.5, PM10, NO₂, SO₂, CO and O₃.

**4. What are PM2.5 and PM10?**
Particulate matter with diameter ≤ 2.5 µm and ≤ 10 µm. PM2.5 is more dangerous because it
goes deep into the lungs and bloodstream.

**5. What is a sub-index?**
The AQI value of one pollutant alone, found from that pollutant's breakpoint table.

**6. How is the overall AQI found from the sub-indices?**
It is the maximum sub-index – the worst pollutant decides the air quality.

**7. What is the dominant pollutant?**
The pollutant whose sub-index is the highest, i.e. the one responsible for the AQI value.

**8. Why do you average over 24 hours or 8 hours instead of using the current reading?**
The NAQI standard defines the breakpoints for 24-hour averages (PM, NO₂, SO₂) and 8-hour
averages (CO, O₃), because health effects depend on exposure over time. Using one hourly
value with these breakpoints would be incorrect.

**9. What happens if some data is missing?**
Missing or negative values are ignored. If fewer than 16 of 24 hours (or 6 of 8) are valid,
that pollutant's average is not used. If fewer than three pollutants remain, or neither PM2.5
nor PM10 is available, the app shows "AQI N/A" with the reason instead of guessing.

**10. Why is CO divided by 1000?**
The API gives CO in µg/m³ but the NAQI table for CO is in mg/m³; 1 mg = 1000 µg.

### APIs and data

**11. Which API do you use?**
Open-Meteo Air Quality API by default (free, no key). Optionally OpenWeatherMap's Air
Pollution API when a key is added to `.env`. Both are first called through their geocoding
API to convert the city name into latitude and longitude.

**12. What is geocoding?**
Converting a place name (e.g. "Pune, India") into coordinates (latitude 18.52, longitude 73.86).

**13. Is the live data from government monitoring stations?**
No. Open-Meteo uses the Copernicus (CAMS) atmospheric model; OpenWeatherMap also provides
modelled estimates. I mention this in the app and the limitations.

**14. OpenWeatherMap already gives an AQI. Why not use it?**
OpenWeatherMap's index is its own 1–5 scale, not the Indian NAQI. Mixing them would be
wrong, so I calculate the NAQI myself from the pollutant values and show their index only as
a separately labelled note.

**15. How do you keep the API key secure?**
It is stored in a `.env` file, loaded with python-dotenv and read with `os.getenv()`. The
`.env` file is in `.gitignore`, the key is never written in code, never shown in the UI, and
error messages are written by me so they never contain the URL with the key.

**16. What happens if the internet is down?**
`requests` raises a ConnectionError or Timeout (10-second limit). The app catches it and
shows: "Could not connect… or switch to Sample data mode." The app does not crash.

**17. What is sample-data mode and is it honest?**
It generates demo values for 10 cities with NumPy so the project can be shown offline. Every
screen shows a "SAMPLE DATA – not real measurements" banner, and the database marks those
rows with `is_sample = 1`.

**18. How do you validate the city name?**
Spaces are trimmed, length must be 2–80, and only letters (any language), spaces and
`. , ' - ( )` are allowed. Digits-only or symbols like `<script>` are rejected.

### Database

**19. Why SQLite instead of MySQL?**
SQLite needs no server or installation, stores the whole database in one file, and is built
into Python. For a single-user desktop app it is the simplest correct choice.

**20. What is the primary key of your table?**
`id INTEGER PRIMARY KEY AUTOINCREMENT`.

**21. How do you prevent duplicate records?**
A `UNIQUE (city, observed_at, data_source)` constraint with `INSERT OR IGNORE`.

**22. What is SQL injection and how did you prevent it?**
An attack where user text changes the SQL command. I use parameterised queries with `?`
placeholders, so input is always treated as data. A test checks this with
`Delhi' OR '1'='1`.

**23. Why store times in UTC?**
APIs return UTC, and UTC has no daylight-saving or time-zone confusion. The app shows both
UTC and local time.

**24. How does CSV export work?**
The filtered records (a Pandas DataFrame) are converted with `to_csv()` and given to
`st.download_button`. UTF-8 with BOM is used so Excel shows µ and ₂ correctly.

### Streamlit, charts and testing

**25. How does Streamlit work?**
It runs the Python script from top to bottom every time the user interacts. `st.session_state`
keeps values (like the current result) between reruns, and `st.cache_data` stores API results
for 10 minutes.

**26. Why cache the API results?**
To avoid calling the API again on every click – the app is faster and stays within the free
rate limits.

**27. Which charts are used and why?**
A gauge for the single AQI value, bar charts to compare pollutants (sub-index chart because
pollutants have different units), a line chart for the hourly trend and history, and a bar
chart for city comparison.

**28. Why is CO not in the same bar chart as other pollutants?**
CO values are in the thousands of µg/m³ and would make the other bars look tiny. It is shown
separately, and the sub-index chart compares all six on the same 0–500 scale.

**29. How did you test the project?**
80 automated pytest tests for AQI maths, averaging rules, categories, hourly timeline, health
advice, database, CSV, input
validation and API error handling (API calls are faked with `monkeypatch`). I also ran the
whole app through Streamlit's `AppTest` on every page in sample and live mode.

**30. When do you allow city comparison?**
Only when all cities use the same AQI standard and the same data source, and only cities with
a valid AQI are plotted; failures are listed as warnings.

**31. What are the limitations?**
Model data rather than station data, no NH₃/Pb, assumed upper limits in the Severe band,
internet needed for live mode, local single-user storage.

**32. What would you add in future?**
Official CPCB station data, IoT sensors, my own ML-based forecasting, email/SMS alerts, and
cloud deployment.

**33. How does the 24-hour outlook work? Is it your own prediction?**
No, I do not predict pollution myself. Open-Meteo (and OpenWeatherMap) provide model forecasts
of hourly pollutant levels. For every future hour I apply the same NAQI rules – 24 h / 8 h
rolling averages of past plus forecast values – to get an estimated AQI. It is always labelled
"forecast (estimate)" and drawn as a dashed line.

**34. What is a rolling AQI?**
The AQI recalculated every hour using the averages that end at that hour. The Outlook chart
shows it for the past 24 hours and the next 24 hours, so you can see whether the air is
improving or getting worse.

**35. How is the health advice personalised?**
Each category has a risk level from 0 to 3. If the user chooses a sensitive profile (children
or older adults, asthma, heart disease, pregnancy), the risk level is raised by one, so they
get more cautious tips and a stricter activity guide. It is still general information, not
medical advice.

**36. Why did you split the app into several page files?**
Streamlit's `st.navigation` lets each page be a short separate script. This keeps every file
small and easy to read, and shared code (search, data loading) lives once in `ui.py`.

---

## 7. Presentation script (about 4 minutes)

**[Slide/Screen 1 – Title]**
"Good morning, ma'am/sir. My project is the **Air Quality Monitoring System Using Python**.
It helps people understand how polluted the air is in any city and what they should do
about it."

**[Problem]**
"Pollution data like 'PM2.5 is 102 micrograms per cubic metre' means nothing to most people.
Also, many apps show an 'AQI' without saying which standard they use. My project converts raw
data into India's official National Air Quality Index from CPCB and explains it in simple
words."

**[Architecture]**
"The project is split into small modules. `app.py` shows the sidebar settings and the menu,
and each page is a short file in `app_pages/`. `api_service.py` gets past and forecast data
from Open-Meteo, or OpenWeatherMap if a key is configured. `aqi_calculator.py` does the AQI
calculation, `health_advice.py` personalises the advice, `database.py` stores the history in
SQLite, `visualizations.py` makes the Plotly charts and maps, and `sample_data.py` provides
offline demo data."

**[Demo – Home]** *(Sample mode → click the Delhi button)*
"I click Delhi. The app shows the AQI card in the official CPCB colour, how the AQI changed
in the last 24 hours, the main pollutant and the last-updated time. Because the AQI is above
my alert level, a pop-up alert appears, and there is a health warning with recommendations
and an activity guide. If I change my health profile to 'Asthma', the advice becomes more
cautious. This banner clearly says this is sample data, and I can download a report."

**[Demo – Live]** *(Switch to Open-Meteo → type your city)*
"Now I switch to live data and search my own city. The app geocodes the city, downloads the
last 24 hours of hourly data and calculates the AQI."

**[AQI calculation]** *(AQI guide → calculator: change PM10 and watch the AQI change)*
"The calculation follows CPCB rules. PM2.5, PM10, NO₂ and SO₂ are averaged over 24 hours, CO
and O₃ over 8 hours. Each average is converted to a sub-index by linear interpolation in the
breakpoint table, and the highest sub-index is the AQI. If fewer than three pollutants are
available, or there is no PM2.5 or PM10, the app does not show an AQI, because the standard
does not allow it."

**[Demo – Outlook]**
"The Outlook page calculates the AQI for every hour of the last 24 hours and, using the
provider's model forecast, the next 24 hours - shown dashed because it is an estimate. It also
suggests the cleanest hours to go outside."

**[Demo – History]** *(History → Add 7 days → filter → Export)*
"Every search is saved in SQLite. I can filter by city, date and live or sample data, see the
AQI trend with the category bands, and export the records to CSV for Excel."

**[Demo – Compare]**
"Here I compare Delhi, Mumbai and Bengaluru. The app only compares values from the same
standard and source, so the comparison is fair. The map shows each city in its category
colour."

**[Quality]**
"I handled errors such as wrong city names, no internet and invalid API keys. The API key is
kept in a `.env` file and never appears in the code. I wrote 80 automated tests, and all of
them pass."

**[Conclusion]**
"In future I would like to add official station data, IoT sensors and my own ML forecasting.
Thank you. I am happy to answer your questions."

---

## 8. Last-minute checklist before the viva

- [ ] `pip install -r requirements.txt` done on the laptop you will use.
- [ ] App starts with `streamlit run app.py`.
- [ ] Sample mode works with Wi-Fi **off** (your backup if college internet fails).
- [ ] "Add 7 days of sample history" clicked so History and trend chart have data.
- [ ] `python -m pytest -v` shows all tests passing (screenshot it).
- [ ] You can write the sub-index formula and the PM2.5 = 45 → 75 example from memory.
- [ ] Screenshots inserted in `docs/PROJECT_REPORT.md` (Section 16).
