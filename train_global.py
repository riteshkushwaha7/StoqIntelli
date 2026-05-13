from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd
import time
import yfinance as yf

from data.fetcher import MarketDataFetcher
from pipeline.trainer import LSTMTrainer, TIMEFRAME_FETCH_CONFIG
from supported_symbols import MODEL_SUPPORTED_TICKERS, resolve_market_ticker

DEFAULT_SYMBOLS = [("RELIANCE", "__GLOBAL__")]
DEFAULT_SYMBOLS.extend((symbol, symbol) for symbol in MODEL_SUPPORTED_TICKERS.keys())  # Share the canonical list.

EPOCHS = 6
LOOKBACK = 60
BATCH_SIZE = 32
LEARNING_RATE = 0.001


def fetch_stock(ticker_ns: str, interval: str | None = None, period: str = "max") -> pd.DataFrame | None:
    for attempt in range(5):
        try:
            history_kwargs = {"period": period, "auto_adjust": True}
            if interval:
                history_kwargs["interval"] = interval
            df = yf.Ticker(ticker_ns).history(**history_kwargs)
            if df is not None and len(df) > 50:
                return df
        except Exception as exc:
            print(f"Attempt {attempt + 1} failed: {exc}")
        time.sleep(3 * (attempt + 1))
    return None


def train_symbols(pairs: Iterable[tuple[str, str]]) -> list[dict[str, object]]:
  fetcher = MarketDataFetcher()
  trainer = LSTMTrainer(saved_models_dir=Path(__file__).resolve().parent / "saved_models")
  summary: list[dict[str, object]] = []

  for base_symbol, model_symbol in pairs:
    ticker_symbol = resolve_market_ticker(base_symbol)
    for timeframe, cfg in TIMEFRAME_FETCH_CONFIG.items():
      try:
        raw_frame = fetch_stock(ticker_symbol, interval=cfg["interval"], period="max")
        if raw_frame is None:
          raise ValueError(f"No market data found for symbol={base_symbol} interval={cfg['interval']}")

        frame = fetcher._sanitize_dataframe(raw_frame)

        info = trainer.train_for_timeframe(
          frame=frame,
          timeframe=timeframe,
          symbol=model_symbol,
          epochs=EPOCHS,
          lookback=LOOKBACK,
          batch_size=BATCH_SIZE,
          learning_rate=LEARNING_RATE,
        )
        summary.append({
          "symbol": model_symbol,
          "base_symbol": base_symbol,
          "timeframe": timeframe,
          "status": "ok",
          **info
        })
      except Exception as exc:  # pragma: no cover - training diagnostics
        summary.append({
          "symbol": model_symbol,
          "base_symbol": base_symbol,
          "timeframe": timeframe,
          "status": "error",
          "detail": str(exc)
        })
    time.sleep(2)
  return summary


def main() -> None:
  summary = train_symbols(DEFAULT_SYMBOLS)
  print(json.dumps(summary, indent=2))


if __name__ == "__main__":
  main()
