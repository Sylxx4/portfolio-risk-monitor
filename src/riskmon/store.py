import sqlite3
from pathlib import Path

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


def init_db(path: Path = None) -> None:
    # : if path is None, use config.DB_PATH; ensure parent directory exists; connect to SQLite; execute SCHEMA; close connection.
    if path is None:
        path = config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)    
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.close()    