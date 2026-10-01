# Scaffold structure; provider logic I write lives in the concrete classes.
from abc import ABC, abstractmethod
from datetime import date

import pandas as pd


class ProviderError(Exception):
    """Raised when a data source cannot satisfy a request."""


class PriceProvider(ABC):
    @abstractmethod
    def get_prices(self, tickers: list[str], start: date, end: date) -> pd.DataFrame:
        """Return adjusted closes as a DataFrame. See the contract."""