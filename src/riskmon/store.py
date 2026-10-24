import sqlite3
from datetime import date, datetime, timedelta, timezone
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

    
def load_prices(tickers: list[str], start: date, end: date, path: Path | None = None) -> pd.DataFrame:
    if path is None:
        path = config.DB_PATH

    tickers = [t.strip().upper() for t in tickers]

    # Build the SQL. The ? placeholders are filled safely by SQLite — NEVER
    # put ticker values directly into the string (that's SQL injection).
    placeholders = ",".join("?" for _ in tickers)
    sql = f"""
        SELECT ticker, date, adj_close
        FROM prices
        WHERE ticker IN ({placeholders})
        AND date >= ?
        AND date <= ?
        ORDER BY date
    """
    params = [*tickers, start.isoformat(), end.isoformat()]

    conn = sqlite3.connect(path)
    long = pd.read_sql_query(sql, conn, params=params, parse_dates=["date"])
    conn.close()

    # : reshape long -> wide and clean to the contract:
    df = long.pivot(index="date", columns="ticker", values="adj_close")
    df = df.reindex(columns=tickers)
    df.index.name = "date"
    df.columns.name = None   #(pivot leaves a stray "ticker" label; clear it)
    df = df.astype("float64")
    return df

    


def missing_ranges(ticker: str, start: date, end: date, path: Path | None = None) -> list[tuple[date, date]]:
    if path is None:
        path = config.DB_PATH
    ticker = ticker.strip().upper()

    # Look up the covered span for this ticker from the coverage table.
    conn = sqlite3.connect(path)
    row = conn.execute(
        "SELECT MIN(start_date), MAX(end_date) FROM coverage WHERE ticker = ?",
        (ticker,),
    ).fetchone()
    conn.close()

    covered_start, covered_end = row  # these are ISO strings, or (None, None) if nothing covered

    # Case 1: nothing covered at all -> the whole requested range is missing.
    # YOU: if covered_start is None, return [(start, end)]
    if covered_start is None:
        return [(start, end)]

    # Parse the covered strings into date objects for comparison.
    covered_start = date.fromisoformat(covered_start)
    covered_end = date.fromisoformat(covered_end)

    gaps = []
    # Case 2: requested start is before covered start -> need the earlier slice.
    # YOU: if start < covered_start:
    #          append (start, covered_start - one day) to gaps
    #      (use timedelta(days=1) to step back one day)
    if start < covered_start:
        gaps.append((start, covered_start - timedelta(days=1)))

    # Case 3: requested end is after covered end -> need the later slice.
    # YOU: if end > covered_end:
    #          append (covered_end + one day, end) to gaps
    if end > covered_end:
        gaps.append((covered_end + timedelta(days=1), end))

    return gaps


#saves coverage information to the database
def record_coverage(ticker: str, start: date, end: date, path: Path | None = None) -> None:
    if path is None:
        path = config.DB_PATH
    ticker = ticker.strip().upper()
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO coverage VALUES (?, ?, ?)",
        (ticker, start.isoformat(), end.isoformat()),
    )
    conn.commit()
    conn.close()

   