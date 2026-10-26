# 🌍 Air Quality Monitoring System Using Python

A Streamlit web application that monitors air pollution in cities, calculates the
**Air Quality Index (AQI) using India's National AQI (CPCB)**, shows interactive charts,
gives general health recommendations, stores history in SQLite, and compares cities.

It works in three data modes:

| Mode | Internet | API key | Notes |
|---|---|---|---|
| 🧪 **Sample data (demo)** | Not needed | Not needed | Built-in demo values, clearly labelled. Best for viva. |
| 🛰️ **Open-Meteo (live)** | Needed | **Not needed** | Free, modelled data (Copernicus CAMS). |
| 🛰️ **OpenWeatherMap (live)** | Needed | Needed (free) | Appears only after you add a key to `.env`. |

---

## 1. Features

- **Home** – city search with quick-pick and recent-city buttons, colour-coded AQI card,
  24-hour AQI sparkline with change, gauge, main pollutant, health warning,
  **personalised advice** for your health profile, **activity guide** (OK / Limit / Avoid),
  **downloadable text report**, and two graphs: hourly AQI trend and "which pollutant
  decides the AQI".
- **Pollutants** – PM2.5, PM10, NO₂, SO₂, CO, O₃ with units, averages, sub-index bars;
  graphs: concentrations, sub-indices, **all six pollutants in small charts** (past 24 h +
  forecast), a closer look at one pollutant, and a location map.
- **Outlook** – hourly AQI for the past 24 h and the **next 24 h (forecast estimate)**, trend
  (improving / stable / worse), expected peak, and the **best hours to go outside**.
- **Compare** – 2–6 cities (pick or type any city): cleanest vs most polluted, AQI ranking
  chart, pollutant breakdown per city, **map**, ranked table (only compatible values).
- **History** – every search saved in SQLite; filters; summary numbers; AQI trend graph;
  **daily AQI heatmap** (city × day); pollutant-over-time graph; category distribution;
  per-city summary; **export to CSV**; demo tools.
- **AQI guide** – categories, formula, breakpoint table and an **interactive AQI calculator**
  that shows each step.
- **Sidebar settings** – data source, health profile, **AQI alert level** (pop-up alert),
  auto-save, and a "How to use this app" help window.

---

## 2. Folder structure

```
air_quality_monitor/
│   app.py                  ← entry point: sidebar settings + navigation (run this)
│   ui.py                   ← shared helpers: city search, AQI card, report download
│   api_service.py          ← gets data (past + forecast): sample / Open-Meteo / OpenWeatherMap
│   aqi_calculator.py       ← averages, sub-indices, AQI, categories, hourly AQI timeline
│   health_advice.py        ← personalised tips + activity guide per health profile
│   database.py             ← SQLite storage, filters, CSV export
│   visualizations.py       ← Plotly charts
│   sample_data.py          ← offline demo data
│   requirements.txt        ← Python libraries
│   README.md               ← this file
│   .env.example            ← template for your API key
│   .gitignore
├── .streamlit/config.toml  ← colour theme
├── app_pages/              ← one file per page
│   home.py · pollutants.py · outlook.py · compare.py · history.py · guide.py · about.py
├── .vscode/                ← VS Code run button + interpreter settings
├── data/                   ← air_quality.db is created here automatically
├── docs/
│   PROJECT_REPORT.md       ← full college project documentation
│   VIVA_PREPARATION.md     ← explanations, 36 viva Q&A, presentation script
└── tests/
    conftest.py
    test_aqi_calculator.py
    test_api_service.py
    test_database.py
    test_health_and_timeline.py
```

---

## 3. Installation on Windows (step by step)

**Step 1 – Install Python 3.10 or newer** (tested with Python 3.13.5)
Download from <https://www.python.org/downloads/>. During setup **tick “Add python.exe to PATH”**.
Check in a new terminal:

```powershell
python --version
```

**Step 2 – Install VS Code** from <https://code.visualstudio.com/> and install the
**Python** extension (by Microsoft) from the Extensions panel (Ctrl+Shift+X).

**Step 3 – Open the project folder**
VS Code → *File → Open Folder…* → select the `air_quality_monitor` folder
(the one that contains `app.py`).

**Step 4 – Open a terminal** in VS Code: *Terminal → New Terminal* (Ctrl + `).

**Step 5 – Create a virtual environment** (a private folder for this project's libraries):

```powershell
python -m venv venv
```

**Step 6 – Activate it:**

```powershell
.\venv\Scripts\Activate.ps1
```

You should now see `(venv)` at the start of the terminal line.
If you get *"running scripts is disabled on this system"*, run this once and try again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

(Using Command Prompt instead? Run `venv\Scripts\activate.bat`.)

**Step 7 – Install the libraries:**

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Step 8 – Select the interpreter in VS Code:** press Ctrl+Shift+P → *Python: Select Interpreter*
→ choose the one showing `.\venv\Scripts\python.exe`.

---

## 4. Configuring an API key (optional)

The app works **without any key** (Sample mode and Open-Meteo). To also enable OpenWeatherMap:

1. Create a free account at <https://home.openweathermap.org/users/sign_up>.
2. Open <https://home.openweathermap.org/api_keys> and copy your key.
3. In the project folder, copy the template:

   ```powershell
   copy .env.example .env
   ```

4. Open `.env` and replace the placeholder:

   ```
   OPENWEATHER_API_KEY=paste_your_real_key_here
   ```

5. Restart the app. The sidebar will say **“OpenWeatherMap key: configured”** and a new data
   source option appears.

🔒 **Security:** `.env` is listed in `.gitignore`, so it is never uploaded to GitHub. The key is
read with `os.getenv()` – it is never written in the code and never shown in the app or in
error messages. New OpenWeatherMap keys can take up to ~2 hours to become active.

---

## 5. Running the application

**Easiest – double-click `run_app.bat`** in the `college project` folder (one level above
`air_quality_monitor`). It goes into the right folder and starts the app with your virtual
environment.

**Option A – Terminal:** first make sure you are **inside the `air_quality_monitor` folder**
(the one containing `app.py`), otherwise Streamlit says *“File does not exist: app.py”*:

```powershell
cd air_quality_monitor
streamlit run app.py
```

Your browser opens at <http://localhost:8501>. Stop the app with **Ctrl + C** in the terminal.

**Option B – VS Code Run button:** open the *Run and Debug* panel (Ctrl+Shift+D), choose
**“Run Air Quality Monitor (Streamlit)”** and press **F5**.

### Quick demo (2 minutes)

1. Sidebar → Data source **Sample data (demo)** → **Home** → click the **Delhi** quick-pick button.
2. Change **My health profile** to *Asthma or lung disease* – the advice and activity guide change.
3. Open **Pollutants** (six pollutants, sub-index bars, charts) and **Outlook** (next 24 hours).
4. **Compare** → Delhi, Mumbai, Bengaluru → *Compare* → try the *Map* view.
5. **History** → *Demo tools* → **Add 7 days of sample history** → *AQI trend*, *Categories*,
   *Export to CSV*.
6. **AQI guide** → change the numbers in the calculator to explain the formula live.
7. Switch to **Open-Meteo (live)** and search your own city to show real data.

---

## 6. Running the tests

```powershell
python -m pytest -v
```

The tests check AQI maths, categories, averaging rules, database storage and filters,
SQL-injection safety, CSV export, city-name validation, and API error handling
(network calls are faked, so tests run offline).

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| `'python' is not recognized` | Reinstall Python and tick **Add to PATH**, or use `py` instead of `python`. Open a new terminal afterwards. |
| `running scripts is disabled on this system` | `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |
| `ModuleNotFoundError: No module named 'streamlit'` | The venv is not active. Run `.\venv\Scripts\Activate.ps1`, then `pip install -r requirements.txt`. In VS Code select the venv interpreter. |
| `Error: Invalid value: File does not exist: app.py` | You are in the wrong folder. Run `cd air_quality_monitor` first, or double-click `run_app.bat`. |
| Terminal stops at **“Email:”** and nothing opens | Streamlit's first-run question. Already disabled in `.streamlit/config.toml`; if you still see it, just press **Enter**. |
| `'streamlit' is not recognized` | Use `python -m streamlit run app.py`. |
| `Port 8501 is already in use` | Close the other Streamlit window, or run `streamlit run app.py --server.port 8502`. |
| “Could not connect to Open-Meteo …” | No internet, firewall or college Wi-Fi blocking. Switch to **Sample data** mode. |
| `CERTIFICATE_VERIFY_FAILED` (SSL) | Already handled with the `truststore` library (uses the Windows certificate store). Make sure `pip install -r requirements.txt` was run. |
| “City … was not found” | Check spelling or add the country: `Pune, India` (Open-Meteo) / `Pune,IN` (OpenWeatherMap). |
| “rejected the API key” | Check the key in `.env` (no quotes, no spaces). New keys need up to 2 hours to activate. |
| OpenWeatherMap option missing | `.env` file missing, wrongly named (`.env.txt`), or still has `your_api_key_here`. Restart the app after editing. |
| AQI shows **N/A** | The source returned fewer than 3 pollutants or not enough hours for the averages – the app refuses to guess. |
| Want to reset history | Close the app and delete `data/air_quality.db` (it is recreated automatically). |
| Project inside OneDrive/a folder with spaces | Works, but always keep paths in quotes, e.g. `cd "C:\Users\you\OneDrive\Desktop\college project\air_quality_monitor"`. |

---

## 8. Important notes

- **AQI standard:** India NAQI (CPCB, 2014). Provider indices (e.g. OpenWeatherMap's 1–5
  scale) are shown only for reference and never mixed with our AQI.
- **Live data are model estimates** for a location (Open-Meteo/CAMS, OpenWeatherMap), not
  official readings from a specific CPCB monitoring station.
- **Sample data are not real measurements.** They are always labelled “SAMPLE DATA”.
- Health recommendations are **general information, not medical advice**.

Documentation: see [`docs/PROJECT_REPORT.md`](docs/PROJECT_REPORT.md) and
[`docs/VIVA_PREPARATION.md`](docs/VIVA_PREPARATION.md).
