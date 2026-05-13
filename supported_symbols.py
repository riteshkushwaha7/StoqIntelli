"""Central mapping for dedicated LSTM stock coverage."""
from __future__ import annotations

# Canonical NSE symbols map to their Yahoo Finance tickers for pre-trained bundles.
SUPPORTED_STOCKS: dict[str, str] = {
    "RELIANCE": "RELIANCE.NS",
    "VBL": "VBL.NS",
    "RVNL": "RVNL.NS",
    "TATATECH": "TATATECH.NS",
    "INFY": "INFY.NS",
    "KPITTECH": "KPITTECH.NS",
    "DMART": "DMART.NS",
    "TATAELXSI": "TATAELXSI.NS",
}

# Backwards-compatible alias for existing imports.
MODEL_SUPPORTED_TICKERS = SUPPORTED_STOCKS


def _normalize(symbol: str) -> str:
    return symbol.strip().upper().replace(" ", "")


def resolve_market_ticker(symbol: str) -> str:
    """Return the Yahoo Finance ticker (always falling back to .NS)."""
    normalized = _normalize(symbol)
    if "." in normalized or normalized.startswith("^") or normalized.endswith("=X"):
        return normalized

    base_key = normalized.split(".")[0]
    override = SUPPORTED_STOCKS.get(base_key)
    if override:
        return override
    return f"{base_key}.NS"


def resolve_exchange_symbol(symbol: str) -> str:
    """Return the NSE symbol (without the .NS suffix) for quote APIs."""
    ticker = resolve_market_ticker(symbol)
    return ticker[:-3] if ticker.endswith(".NS") else ticker
