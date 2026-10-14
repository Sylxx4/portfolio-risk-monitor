from unittest.mock import MagicMock, patch

import pytest

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