from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

import pandas as pd
import requests
import yfinance as yf

from data.cache import HybridCache


DEFAULT_PERIOD_BY_INTERVAL: dict[str, str] = {
    # Yahoo restricts 15m requests to the most recent 60 days.
    # Using "2mo" can occasionally exceed 60 days (month-length dependent),
    # which causes "possibly delisted" false negatives.
    "15m": "60d",
    "1d": "5y",
}


class MarketDataFetcher:
    def __init__(self, cache: HybridCache | None = None, nse_timeout: int = 8) -> None:
        self.cache = cache
        self.nse_timeout = nse_timeout
        self._nse_session = requests.Session()
        self._nse_session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
                ),
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.nseindia.com/",
            }
        )

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return symbol.strip().upper().replace(" ", "")

    def fetch_ohlcv(
        self, symbol: str, interval: str = "1d", period: str | None = None
    ) -> pd.DataFrame:
        normalized = self.normalize_symbol(symbol)
        resolved_period = period or DEFAULT_PERIOD_BY_INTERVAL.get(interval, "1y")
        cache_key = f"ohlcv:{normalized}:{interval}:{resolved_period}"

        if self.cache:
            cached_payload = self.cache.get(cache_key)
            if cached_payload:
                return self._from_records(cached_payload)

        ticker_candidates = self._ticker_candidates(normalized)
        frame = pd.DataFrame()
        for ticker_symbol in ticker_candidates:
            data = yf.Ticker(ticker_symbol).history(
                period=resolved_period,
                interval=interval,
                auto_adjust=False,
                actions=False,
                prepost=False,
            )
            if not data.empty:
                frame = data
                break

        if frame.empty:
            raise ValueError(f"No market data found for symbol={symbol} interval={interval}")

        frame = self._sanitize_dataframe(frame)
        if self.cache:
            self.cache.set(cache_key, self._to_records(frame), ttl_seconds=45)
        return frame

    def fetch_live_quote(self, symbol: str) -> dict[str, Any]:
        normalized = self.normalize_symbol(symbol)
        cache_key = f"quote:{normalized}"
        if self.cache:
            cached_quote = self.cache.get(cache_key)
            if cached_quote:
                return cached_quote

        quote = self._fetch_nse_quote(normalized)
        if quote is None:
            quote = self._fetch_yfinance_quote(normalized)

        if self.cache and quote is not None:
            self.cache.set(cache_key, quote, ttl_seconds=12)
        return quote or {}

    def fetch_news_rss_url(self, symbol: str) -> str:
        normalized = self.normalize_symbol(symbol)
        query = quote_plus(f"{normalized} stock")
        return f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    def _ticker_candidates(self, symbol: str) -> list[str]:
        if "." in symbol or symbol.startswith("^") or symbol.endswith("=X"):
            return [symbol]
        if symbol.isalpha():
            return [f"{symbol}.NS", symbol]
        return [symbol]

    def _sanitize_dataframe(self, frame: pd.DataFrame) -> pd.DataFrame:
        clean = frame.copy()
        clean.columns = [str(column).lower() for column in clean.columns]
        for column in ["open", "high", "low", "close", "volume"]:
            if column not in clean.columns:
                clean[column] = 0.0

        clean = clean[["open", "high", "low", "close", "volume"]]
        clean.index = pd.to_datetime(clean.index).tz_localize(None)
        clean.index.name = "timestamp"
        clean = clean.dropna()
        return clean

    def _to_records(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        records = frame.reset_index().to_dict(orient="records")
        for row in records:
            row["timestamp"] = pd.Timestamp(row["timestamp"]).isoformat()
        return records

    def _from_records(self, records: list[dict[str, Any]]) -> pd.DataFrame:
        frame = pd.DataFrame(records)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        frame = frame.set_index("timestamp")
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna()
        return frame

    def _fetch_yfinance_quote(self, symbol: str) -> dict[str, Any] | None:
        candidates = self._ticker_candidates(symbol)
        for ticker_symbol in candidates:
            hist = yf.Ticker(ticker_symbol).history(period="2d", interval="1d", actions=False)
            if hist.empty:
                continue

            hist = hist.tail(2)
            last_close = float(hist["Close"].iloc[-1])
            prev_close = float(hist["Close"].iloc[0]) if len(hist) > 1 else last_close
            delta = last_close - prev_close
            delta_pct = (delta / prev_close * 100.0) if prev_close else 0.0
            volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
            return {
                "source": "yfinance",
                "price": round(last_close, 4),
                "change": round(delta, 4),
                "change_percent": round(delta_pct, 4),
                "volume": volume,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        return None

    def _fetch_nse_quote(self, symbol: str) -> dict[str, Any] | None:
        try:
            self._nse_session.get("https://www.nseindia.com", timeout=self.nse_timeout)
            response = self._nse_session.get(
                f"https://www.nseindia.com/api/quote-equity?symbol={symbol}",
                timeout=self.nse_timeout,
            )
            if response.status_code != 200:
                return None
            payload = response.json()
        except Exception:
            return None

        price_info = payload.get("priceInfo", {})
        market_data = payload.get("securityInfo", {})
        last_price = price_info.get("lastPrice")
        if last_price is None:
            return None

        return {
            "source": "nse",
            "price": float(last_price),
            "change": float(price_info.get("change", 0.0)),
            "change_percent": float(price_info.get("pChange", 0.0)),
            "volume": int(market_data.get("issuedSize", 0) or 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
