from datetime import date

import pandas as pd
import requests

from riskmon import config
from riskmon.providers.base import PriceProvider


class AlpacaProvider(PriceProvider):
    BASE_URL = "https://data.alpaca.markets/v2/stocks/{ticker}/bars"

    def get_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame:
        ticker = tickers[0].strip().upper()
        headers = {
            # YOU: two headers, values from config.require(...)
            "APCA-API-KEY-ID": config.require("ALPACA_KEY_ID"),
            "APCA-API-SECRET-KEY": config.require("ALPACA_SECRET_KEY")
        }
        params = {
            # YOU: timeframe, start, end (use .isoformat()), feed, adjustment
            "timeframe": "1Day",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "feed": "iex",
            "adjustment": "all",
        }
        url = self.BASE_URL.format(ticker=ticker)
        response = requests.get(url, headers=headers, params=params, timeout=config.HTTP_TIMEOUT)
        bars = response.json()["bars"]

        # YOU: build the DataFrame
        # - make a Series of the "c" values, indexed by the "t" values
        closes = [bar["c"] for bar in bars]
        timestamps = [bar["t"] for bar in bars]
        # - convert the index with pd.to_datetime(...) then normalize to plain dates
        df = pd.DataFrame({ticker: closes}, index=pd.to_datetime(timestamps, utc=True))
        # - name the column after the ticker
        # - name the index "date"
        # return the DataFrame
        df.index = df.index.tz_convert("America/New_York").normalize().tz_localize(None)
        df.index.name = "date"
        df = df.astype("float64")
        return df