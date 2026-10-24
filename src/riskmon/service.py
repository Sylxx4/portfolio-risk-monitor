from datetime import date

import pandas as pd

from riskmon import store
from riskmon.config import get_provider


#fetches price data for the given tickers and dates, caching results
def get_prices_cached(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    store.init_db()  # make sure tables exist
    tickers = [t.strip().upper() for t in tickers] # tickers stripped and uppercased
    provider = get_provider()  # provider instance

    for ticker in tickers:
        gaps = store.missing_ranges(ticker, start, end)
        for gap_start, gap_end in gaps: # loop through each missing range
            df = provider.get_prices([ticker], gap_start, gap_end) # fetch prices for the specific gap
            store.save_prices(df, source="alpaca") #save the fetched prices
        store.record_coverage(ticker, start, end) # record coverage for the WHOLE requested range (start, end),
    
    return store.load_prices(tickers, start, end) # After filling all gaps, serve the full range from disk. 