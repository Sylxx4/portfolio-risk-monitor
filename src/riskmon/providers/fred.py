from datetime import date

import pandas as pd
import requests

from riskmon import config
from riskmon.providers.base import ProviderError

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"


def get_series(series_id: str, start: date, end: date) -> pd.Series:
    params = {
        "series_id": series_id,
        "api_key": config.require("FRED_API_KEY"),
        "file_type": "json",
        "observation_start": start.isoformat(),
        "observation_end": end.isoformat(),
    }
    response = requests.get(FRED_URL, params=params, timeout=config.HTTP_TIMEOUT)
    data = response.json()

    # +: error guard — if "error_message" is a key in data,
    #      raise ProviderError with that message.
    if "error_message" in data:
        raise ProviderError(data["error_message"])

    observations = data["observations"]

    # : build the Series:
    values = [obs["value"] for obs in observations]
    dates  = [obs["date"]  for obs in observations]
    s = pd.Series(values, index=pd.to_datetime(dates))
    s = pd.to_numeric(s, errors="coerce")   # turns "." into NaN
    s.name = series_id
    return s