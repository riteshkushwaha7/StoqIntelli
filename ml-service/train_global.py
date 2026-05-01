from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from data.fetcher import MarketDataFetcher
from pipeline.trainer import LSTMTrainer, TIMEFRAME_FETCH_CONFIG

DEFAULT_SYMBOLS = [
    ("RELIANCE", "__GLOBAL__"),
    ("HDFCBANK", "HDFCBANK"),
    ("BHARTIARTL", "BHARTIARTL"),
    ("SBIN", "SBIN"),
    ("ICICIBANK", "ICICIBANK"),
]

EPOCHS = 6
LOOKBACK = 60
BATCH_SIZE = 32
LEARNING_RATE = 0.001


def train_symbols(pairs: Iterable[tuple[str, str]]) -> list[dict[str, object]]:
  fetcher = MarketDataFetcher()
  trainer = LSTMTrainer(saved_models_dir=Path(__file__).resolve().parent / "saved_models")
  summary: list[dict[str, object]] = []

  for base_symbol, model_symbol in pairs:
    for timeframe, cfg in TIMEFRAME_FETCH_CONFIG.items():
      try:
        frame = fetcher.fetch_ohlcv(symbol=base_symbol, interval=cfg["interval"], period=cfg["period"])
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
  return summary


def main() -> None:
  summary = train_symbols(DEFAULT_SYMBOLS)
  print(json.dumps(summary, indent=2))


if __name__ == "__main__":
  main()
