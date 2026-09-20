import os
import requests
from dotenv import load_dotenv

load_dotenv()


alpaca_key = os.environ["ALPACA_KEY_ID"]
alpaca_secret = os.environ["ALPACA_SECRET_KEY"]
fred_key = os.environ["FRED_API_KEY"]

alpaca_headers = {
    "APCA-API-KEY-ID": alpaca_key,
    "APCA-API-SECRET-KEY": alpaca_secret,
}
alpaca_params = {
    "timeframe": "1Day",
    "start": "2025-01-02",
    "end": "2025-01-11",
    "feed": "iex",
    "adjustment": "all",
}
alpaca_url = "https://data.alpaca.markets/v2/stocks/AAPL/bars"

r = requests.get(alpaca_url, headers=alpaca_headers, params=alpaca_params, timeout=10)

print("Alpaca status:", r.status_code)
bars = r.json()["bars"]
print("First two bars:", bars[:2])

fred_params = {
    "series_id": "CPIAUCSL",
    "api_key": fred_key,
    "file_type": "json",
    "observation_start": "2024-01-01",
}
fred_url = "https://api.stlouisfed.org/fred/series/observations"

fr = requests.get(fred_url, params=fred_params, timeout=10)
print("FRED status:", fr.status_code)
observations = fr.json()["observations"]
print("First two observations:", observations[:2])