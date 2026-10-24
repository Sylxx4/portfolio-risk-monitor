import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DB_PATH = Path(os.getenv("RISKMON_DB", "data/riskmon.db"))
PRICE_PROVIDER = os.getenv("PRICE_PROVIDER", "alpaca")
HTTP_TIMEOUT = 10


def require(name: str) -> str:
    value = os.getenv(name)
    # YOU: if value is missing or empty, raise RuntimeError with a message naming `name`
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    # YOU: otherwise, return value
    return value

def get_provider():
    from riskmon.providers.alpaca import AlpacaProvider
    from riskmon.providers.yfinance_fallback import YFinanceProvider
    if PRICE_PROVIDER == "yfinance":
        return YFinanceProvider()
    return AlpacaProvider()    