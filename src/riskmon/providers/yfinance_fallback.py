from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from riskmon.providers.base import PriceProvider, ProviderError


class YFinanceProvider(PriceProvider):
    def get_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame:
        tickers = [t.strip().upper() for t in tickers]

        # yfinance end is EXCLUSIVE; your contract is inclusive. Add one day.
        raw = yf.download(
            tickers,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),
            auto_adjust=True,
            progress=False,
        )

        # Pull out the Close prices. Multi-ticker -> MultiIndex columns.
        close = raw["Close"]
        # If a single ticker was requested, close may be a Series; make it a DataFrame.
        if isinstance(close, pd.Series):
            close = close.to_frame(tickers[0])

        # YOU: guard — for each requested ticker, if it's missing from close.columns
        #      OR its column is entirely NaN, raise ProviderError naming it.
        for ticker in tickers:
            if ticker not in close.columns or close[ticker].isna().all():
                raise ProviderError(f"Missing required data for symbol: {ticker}")

        #: clean to the contract:

        df = close[tickers]
        df.index = df.index.normalize()
        df.index.name = "date"
        df = df.astype("float64")
        return df