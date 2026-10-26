"""
database.py
===========
Stores air-quality observations in a local SQLite database file
(data/air_quality.db). SQLite is built into Python - no server needed.

Table: observations  (one row = one AQI result for one city at one time)

All SQL uses "?" placeholders (parameterised queries). User input is never
pasted directly into SQL text, which protects against SQL injection.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "air_quality.db"

POLLUTANT_COLUMNS = ["pm2_5", "pm10", "no2", "so2", "co", "o3"]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS observations (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    city               TEXT    NOT NULL,
    country            TEXT,
    latitude           REAL,
    longitude          REAL,
    observed_at        TEXT    NOT NULL,   -- time of the data, UTC 'YYYY-MM-DD HH:MM:SS'
    recorded_at        TEXT    NOT NULL,   -- time the row was saved, UTC
    pm2_5              REAL,               -- 24-hour average, µg/m³
    pm10               REAL,               -- 24-hour average, µg/m³
    no2                REAL,               -- 24-hour average, µg/m³
    so2                REAL,               -- 24-hour average, µg/m³
    co                 REAL,               -- 8-hour average,  µg/m³
    o3                 REAL,               -- 8-hour average,  µg/m³
    aqi                INTEGER,            -- NULL when AQI could not be calculated
    category           TEXT,
    dominant_pollutant TEXT,
    aqi_standard       TEXT    NOT NULL,
    data_source        TEXT    NOT NULL,   -- 'sample', 'open-meteo', 'openweathermap'
    is_sample          INTEGER NOT NULL DEFAULT 0,
    UNIQUE (city, observed_at, data_source)
);
"""

CREATE_INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_city_time ON observations (city, observed_at);"

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _connect(db_path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path)


def to_utc_text(moment: datetime) -> str:
    """Convert a datetime to the UTC text format stored in the database."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime(TIME_FORMAT)


def init_db(db_path=DEFAULT_DB_PATH) -> None:
    """Create the table (only if it does not exist yet)."""
    with closing(_connect(db_path)) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.execute(CREATE_INDEX_SQL)
        conn.commit()


def save_observation(record: dict, db_path=DEFAULT_DB_PATH) -> bool:
    """
    Insert one observation. Returns True if saved, False if the same city,
    time and source were already stored (duplicates are skipped).
    """
    if not record.get("city") or not record.get("observed_at") or not record.get("data_source"):
        raise ValueError("city, observed_at and data_source are required")

    row = {
        "city": record["city"],
        "country": record.get("country"),
        "latitude": record.get("latitude"),
        "longitude": record.get("longitude"),
        "observed_at": to_utc_text(record["observed_at"]),
        "recorded_at": to_utc_text(datetime.now(timezone.utc)),
        **{col: record.get(col) for col in POLLUTANT_COLUMNS},
        "aqi": record.get("aqi"),
        "category": record.get("category"),
        "dominant_pollutant": record.get("dominant_pollutant"),
        "aqi_standard": record.get("aqi_standard", ""),
        "data_source": record["data_source"],
        "is_sample": 1 if record.get("is_sample") else 0,
    }
    columns = ", ".join(row.keys())
    placeholders = ", ".join("?" for _ in row)
    sql = f"INSERT OR IGNORE INTO observations ({columns}) VALUES ({placeholders})"

    with closing(_connect(db_path)) as conn:
        cursor = conn.execute(sql, list(row.values()))
        conn.commit()
        return cursor.rowcount == 1


def get_observations(city: str | None = None, start_date: date | None = None,
                     end_date: date | None = None, data_type: str = "all",
                     db_path=DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Read observations as a pandas DataFrame, newest first.

    city       - exact city name, or None for all cities
    start_date - include rows on/after this date (UTC)
    end_date   - include rows on/before this date (UTC)
    data_type  - "all", "live" or "sample"
    """
    sql = "SELECT * FROM observations WHERE 1 = 1"
    params: list = []
    if city:
        sql += " AND city = ?"
        params.append(city)
    if start_date:
        sql += " AND observed_at >= ?"
        params.append(f"{start_date:%Y-%m-%d} 00:00:00")
    if end_date:
        sql += " AND observed_at <= ?"
        params.append(f"{end_date:%Y-%m-%d} 23:59:59")
    if data_type == "live":
        sql += " AND is_sample = 0"
    elif data_type == "sample":
        sql += " AND is_sample = 1"
    sql += " ORDER BY observed_at DESC, id DESC"

    with closing(_connect(db_path)) as conn:
        frame = pd.read_sql_query(sql, conn, params=params)
    if not frame.empty:
        frame["observed_at"] = pd.to_datetime(frame["observed_at"], utc=True)
        frame["recorded_at"] = pd.to_datetime(frame["recorded_at"], utc=True)
    return frame


def get_cities(db_path=DEFAULT_DB_PATH) -> list[str]:
    with closing(_connect(db_path)) as conn:
        rows = conn.execute("SELECT DISTINCT city FROM observations ORDER BY city").fetchall()
    return [row[0] for row in rows]


def count_observations(db_path=DEFAULT_DB_PATH) -> int:
    with closing(_connect(db_path)) as conn:
        return conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]


def delete_sample_observations(db_path=DEFAULT_DB_PATH) -> int:
    """Remove all sample (demo) rows. Live rows are kept. Returns rows deleted."""
    with closing(_connect(db_path)) as conn:
        cursor = conn.execute("DELETE FROM observations WHERE is_sample = 1")
        conn.commit()
        return cursor.rowcount


def to_csv_bytes(frame: pd.DataFrame) -> bytes:
    """Convert records to CSV bytes for the download button (opens in Excel)."""
    export = frame.copy()
    for col in ("observed_at", "recorded_at"):
        if col in export.columns:
            export[col] = export[col].astype(str)
    return export.to_csv(index=False).encode("utf-8-sig")
