from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from riskmon.providers import fred
from riskmon.providers.alpaca import AlpacaProvider, RetryableError
from riskmon.providers.base import ProviderError


def fake_response(status_code):
    """Build a fake requests response with a chosen status code."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {"bars": {}, "next_page_token": None}
    resp.text = "fake error body"
    return resp


@patch("riskmon.providers.alpaca.requests.get")
@patch("tenacity.nap.time.sleep")
def test_server_error_retries_three_times(mock_sleep,mock_get):
    # Make every call return a 503
    mock_get.return_value = fake_response(503)
    provider = AlpacaProvider()

    # : calling _fetch_page should raise (after retries). Use pytest.raises.
    # : then assert mock_get was called exactly 3 times.
    with pytest.raises(RetryableError):
        provider._fetch_page(headers={}, params={})
    assert mock_get.call_count == 3


@patch("riskmon.providers.alpaca.requests.get")
def test_auth_error_does_not_retry(mock_get):
    # Make the call return a 403
    mock_get.return_value = fake_response(403)
    provider = AlpacaProvider()

    # : calling _fetch_page should raise ProviderError.
    with pytest.raises(ProviderError):
        provider._fetch_page(headers={}, params={})
    # : then assert mock_get was called exactly 1 time (no retry).
    assert mock_get.call_count == 1



@patch("riskmon.providers.fred.requests.get")
def test_fred_dot_becomes_nan(mock_get):
    # Fake FRED response with one good value and one "." missing marker
    fake = MagicMock()
    fake.json.return_value = {
        "observations": [
            {"date": "2024-01-01", "value": "309.698"},
            {"date": "2024-02-01", "value": "."},
        ]
    }
    mock_get.return_value = fake

    s = fred.get_series("CPIAUCSL", date(2024, 1, 1), date(2024, 2, 1))

    # : assert the series has exactly 1 NaN
    # : assert the first value (2024-01-01) equals 309.698 
    assert s.isna().sum() == 1
    assert s.iloc[0] == 309.698   

@patch("riskmon.providers.alpaca.requests.get")
def test_alpaca_contract_shape(mock_get):
    # Fake a multi-ticker Alpaca response (bars keyed by symbol, one page)
    fake = MagicMock()
    fake.status_code = 200
    fake.json.return_value = {
        "bars": {
            "AAPL": [
                {"c": 242.06, "t": "2025-01-02T05:00:00Z"},
                {"c": 241.66, "t": "2025-01-03T05:00:00Z"},
            ],
            "MSFT": [
                {"c": 412.92, "t": "2025-01-02T05:00:00Z"},
                {"c": 418.04, "t": "2025-01-03T05:00:00Z"},
            ],
        },
        "next_page_token": None,
    }
    mock_get.return_value = fake

    df = AlpacaProvider().get_prices(["AAPL", "MSFT"], date(2025, 1, 2), date(2025, 1, 3))


    assert list(df.columns) == ["AAPL", "MSFT"]
    assert df.index.name == "date"
    assert df.index.is_monotonic_increasing
    assert df.dtypes["AAPL"] == "float64"
    assert df.dtypes["MSFT"] == "float64"

@patch("riskmon.providers.alpaca.requests.get")
def test_alpaca_pagination_combines_pages(mock_get):
    # Page 1: AAPL's first day, with a token saying "more exists"
    page1 = MagicMock()
    page1.status_code = 200
    page1.json.return_value = {
        "bars": {"AAPL": [{"c": 242.06, "t": "2025-01-02T05:00:00Z"}]},
        "next_page_token": "TOKEN123",
    }
    # Page 2: AAPL's second day, token None means "last page"
    page2 = MagicMock()
    page2.status_code = 200
    page2.json.return_value = {
        "bars": {"AAPL": [{"c": 241.66, "t": "2025-01-03T05:00:00Z"}]},
        "next_page_token": None,
    }
    # side_effect returns page1 on the first call, page2 on the second
    mock_get.side_effect = [page1, page2]

    df = AlpacaProvider().get_prices(["AAPL"], date(2025, 1, 2), date(2025, 1, 3))

    # YOU: assert requests.get was called exactly 2 times (two pages fetched)
    assert mock_get.call_count == 2
    # YOU: assert the df has 2 rows (both days combined) 
    assert len(df) == 2   