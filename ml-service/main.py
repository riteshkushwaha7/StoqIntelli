from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from data.cache import HybridCache
from data.fetcher import MarketDataFetcher
from data.preprocessor import FeatureEngineer
from pipeline.aggregator import EnsembleAggregator
from pipeline.predictor import PricePredictor
from pipeline.trainer import ALL_TIMEFRAMES, LSTMTrainer

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
CACHE_PATH = BASE_DIR / "data" / "cache.sqlite"
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",") if origin.strip()]

cache = HybridCache(db_path=CACHE_PATH, default_ttl_seconds=60)
fetcher = MarketDataFetcher(cache=cache)
feature_engineer = FeatureEngineer()
aggregator = EnsembleAggregator()
trainer = LSTMTrainer(saved_models_dir=MODEL_DIR, feature_engineer=feature_engineer)
predictor = PricePredictor(
    saved_models_dir=MODEL_DIR,
    fetcher=fetcher,
    feature_engineer=feature_engineer,
    aggregator=aggregator,
)

app = FastAPI(
    title="StoqIntelli ML Service",
    version="1.0.0",
    description="Selected-timeframe LSTM prediction service",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "stoqintelli-ml", "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/stock/{symbol}")
def get_stock_data(
    symbol: str,
    interval: str = Query(default="15m"),
    period: str | None = Query(default=None),
    limit: int = Query(default=250, ge=50, le=2000),
) -> dict:
    try:
        frame = fetcher.fetch_ohlcv(symbol=symbol, interval=interval, period=period)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    featured = feature_engineer.compute_features(frame)
    if featured.empty:
        raise HTTPException(status_code=422, detail="Not enough candles to compute indicators")

    records = _frame_to_records(featured.tail(limit))
    quote = fetcher.fetch_live_quote(symbol)
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "period": period or "auto",
        "quote": quote,
        "candles": records,
    }


@app.get("/predict/{symbol}")
def predict_symbol(
    symbol: str,
    timeframes: str | None = Query(default=None, description="Comma-separated timeframes"),
) -> dict:
    selected_timeframes = _parse_timeframes(timeframes)
    try:
        return predictor.predict_symbol(symbol=symbol, timeframes=selected_timeframes)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc


@app.post("/train/{symbol}")
def train_symbol(
    symbol: str,
    epochs: int = Query(default=16, ge=1, le=400),
    lookback: int = Query(default=60, ge=20, le=500),
    batch_size: int = Query(default=32, ge=8, le=256),
    learning_rate: float = Query(default=0.001, ge=0.00001, le=0.05),
    timeframes: str | None = Query(default=None, description="Comma-separated timeframes"),
) -> dict:
    selected_timeframes = _parse_timeframes(timeframes)
    result = trainer.train_symbol(
        symbol=symbol,
        fetcher=fetcher,
        epochs=epochs,
        lookback=lookback,
        batch_size=batch_size,
        learning_rate=learning_rate,
        timeframes=selected_timeframes,
    )
    return result


def _parse_timeframes(timeframes: str | None) -> list[str] | None:
    if not timeframes:
        return None
    seen: set[str] = set()
    chosen: list[str] = []
    for item in timeframes.split(","):
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        chosen.append(normalized)
        seen.add(normalized)
    invalid = [item for item in chosen if item not in ALL_TIMEFRAMES]
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported timeframes: {', '.join(invalid)}",
        )
    return chosen


def _frame_to_records(frame: pd.DataFrame) -> list[dict]:
    records = frame.reset_index().to_dict(orient="records")
    normalized_records: list[dict] = []
    for row in records:
        cleaned: dict[str, object] = {}
        for key, value in row.items():
            if isinstance(value, pd.Timestamp):
                cleaned[key] = value.isoformat()
            elif isinstance(value, (int, float)):
                cleaned[key] = float(value)
            else:
                cleaned[key] = value
        normalized_records.append(cleaned)
    return normalized_records

