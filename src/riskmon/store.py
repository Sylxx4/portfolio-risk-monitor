import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from riskmon import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    ticker     TEXT NOT NULL,
    date       TEXT NOT NULL,
    adj_close  REAL NOT NULL,
    source     TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS macro (
    series_id  TEXT NOT NULL,
    date       TEXT NOT NULL,
    value      REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (series_id, date)
);

CREATE TABLE IF NOT EXISTS coverage (
    ticker     TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL,
    PRIMARY KEY (ticker, start_date, end_date)
);
"""


def init_db(path: Path | None = None) -> None:
    # : if path is None, use config.DB_PATH; ensure parent directory exists; connect to SQLite; execute SCHEMA; close connection.
    if path is None:
        path = config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)    
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.close()    

def save_prices(df: pd.DataFrame, source: str, path: Path | None = None) -> int:
    if path is None:
        path = config.DB_PATH

    # Step 1: wide -> long
    long = df.reset_index().melt(
        id_vars="date", var_name="ticker", value_name="adj_close"
    )
    # Step 2: drop rows where adj_close is NaN (never store a missing price)
    long = long.dropna(subset=["adj_close"])
    # Step 3: dates as ISO strings (SQLite has no date type)
    long["date"] = long["date"].dt.strftime("%Y-%m-%d")
    # Step 4: add the bookkeeping columns
    long["source"] = source
    long["fetched_at"] = datetime.now(timezone.utc).isoformat()

    # Step 5: write to the prices table
    # :
    rows = list(long[["ticker","date","adj_close","source","fetched_at"]].itertuples(index=False, name=None))
    conn = sqlite3.connect(path)
    conn.executemany("INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    return len(rows)    