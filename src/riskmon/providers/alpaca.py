from datetime import date

import pandas as pd
import requests

from riskmon import config
from riskmon.providers.base import PriceProvider, ProviderError


class AlpacaProvider(PriceProvider):
    BASE_URL = "https://data.alpaca.markets/v2/stocks/{ticker}/bars"
    MULTI_URL = "https://data.alpaca.markets/v2/stocks/bars"

    def _fetch_page(self, headers: dict, params: dict) -> dict:
        #two lines 
        response = requests.get(self.MULTI_URL, headers=headers, params=params, timeout=config.HTTP_TIMEOUT)
        return response.json()


    def get_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame:
        tickers = [t.strip().upper() for t in tickers]
        headers = {
            # two headers, values from config.require(...)
            "APCA-API-KEY-ID": config.require("ALPACA_KEY_ID"),
            "APCA-API-SECRET-KEY": config.require("ALPACA_SECRET_KEY")
        }
        params = {
            #: timeframe, start, end (use .isoformat()), feed, adjustment
            "timeframe": "1Day",
            "start": start.isoformat(),
            "end": end.isoformat(),
            "feed": "iex",
            "adjustment": "all",
            "symbols": ",".join(tickers),
            "limit": 10000,
        }
        collected = {t: [] for t in tickers}
        
        while True:
            page = self._fetch_page(headers, params)
            bars = page["bars"]
            for symbol, bar_list in bars.items():
                collected[symbol].extend(bar_list)
            
            token = page.get("next_page_token")
            if token is None:
                break
            params["page_token"] = token


        # Point 5 [S3]: reject any ticker that came back empty
        for symbol, bar_list in collected.items():
            if not bar_list:
                # raise ProviderError naming the symbol
                raise ProviderError(f"Missing required data for symbol: {symbol}")
                


        # Points 6–7 [S2]: build one clean Series per ticker
        series_dict = {}
        for symbol, bar_list in collected.items():
            closes = [bar["c"] for bar in bar_list]
            timestamps = [bar["t"] for bar in bar_list]
            s = pd.Series(closes, index=pd.to_datetime(timestamps, utc=True))
            s.index = s.index.tz_convert("America/New_York").normalize().tz_localize(None)
            series_dict[symbol] = s


        # Point 8 [S2]: combine into one DataFrame, one column per ticker
        df = pd.concat(series_dict, axis=1)
        df = df[tickers]
        df.index.name = "date"
        df = df.astype("float64")
        return df    
            
            




    