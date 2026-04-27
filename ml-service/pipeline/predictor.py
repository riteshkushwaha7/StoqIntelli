from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from data.fetcher import MarketDataFetcher
from data.preprocessor import FeatureEngineer
from models.lstm_long import build_long_model
from models.lstm_mid import build_mid_model
from models.lstm_short import build_short_model
from models.sentiment import SentimentAnalyzer
from pipeline.aggregator import EnsembleAggregator
from pipeline.trainer import ALL_TIMEFRAMES, TIMEFRAME_FETCH_CONFIG


class PricePredictor:
    def __init__(
        self,
        saved_models_dir: str | Path,
        fetcher: MarketDataFetcher,
        feature_engineer: FeatureEngineer,
        sentiment_analyzer: SentimentAnalyzer,
        aggregator: EnsembleAggregator,
        device: str | None = None,
    ) -> None:
        self.saved_models_dir = Path(saved_models_dir)
        self.fetcher = fetcher
        self.feature_engineer = feature_engineer
        self.sentiment_analyzer = sentiment_analyzer
        self.aggregator = aggregator
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._bundle_cache: dict[str, dict[str, Any]] = {}

    def predict_symbol(self, symbol: str, timeframes: list[str] | None = None) -> dict[str, Any]:
        normalized = symbol.upper()
        raw_predictions: dict[str, dict[str, Any]] = {}
        current_price = None
        skipped_timeframes: list[dict[str, str]] = []
        chosen_timeframes = timeframes or ALL_TIMEFRAMES

        for timeframe in chosen_timeframes:
            config = TIMEFRAME_FETCH_CONFIG[timeframe]
            try:
                frame = self.fetcher.fetch_ohlcv(
                    symbol=normalized,
                    interval=config["interval"],
                    period=config["period"],
                )
                if frame.empty:
                    skipped_timeframes.append({"timeframe": timeframe, "reason": "No data returned"})
                    continue

                if current_price is None:
                    current_price = float(frame["close"].iloc[-1])
                predicted_price, confidence, source = self._predict_for_timeframe(
                    symbol=normalized,
                    timeframe=timeframe,
                    frame=frame,
                    fallback_price=current_price,
                )
                raw_predictions[timeframe] = {
                    "predicted_price": predicted_price,
                    "confidence": confidence,
                    "source": source,
                }
            except Exception as exc:
                skipped_timeframes.append({"timeframe": timeframe, "reason": str(exc)})
                continue

        if current_price is None or not raw_predictions:
            raise ValueError(f"Unable to fetch any market data for {symbol}")

        sentiment = self.sentiment_analyzer.score(normalized).to_dict()
        final_predictions = self.aggregator.combine_predictions(
            current_price=current_price,
            price_predictions=raw_predictions,
            sentiment=sentiment,
        )

        return {
            "symbol": normalized,
            "current_price": round(current_price, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sentiment": sentiment,
            "predictions": final_predictions,
            "skipped_timeframes": skipped_timeframes,
        }

    def _predict_for_timeframe(
        self,
        symbol: str,
        timeframe: str,
        frame: pd.DataFrame,
        fallback_price: float,
    ) -> tuple[float, float, str]:
        featured = self.feature_engineer.compute_features(frame)
        bundle = self._load_model_bundle(symbol, timeframe)
        if bundle is None:
            return self._naive_projection(featured, fallback_price), 0.58, "naive"

        feature_columns = bundle.get("feature_columns", [])
        if not feature_columns or any(column not in featured.columns for column in feature_columns):
            return self._naive_projection(featured, fallback_price), 0.56, "naive"
        lookback = int(bundle.get("lookback", 60))
        sequence = self.feature_engineer.latest_sequence(featured, feature_columns=feature_columns, lookback=lookback)
        if sequence is None:
            return self._naive_projection(featured, fallback_price), 0.55, "naive"

        x_mean = np.asarray(bundle["x_mean"], dtype=np.float32)
        x_std = np.asarray(bundle["x_std"], dtype=np.float32) + 1e-8
        normalized_sequence = (sequence - x_mean) / x_std
        tensor = torch.tensor(normalized_sequence[np.newaxis, ...], dtype=torch.float32, device=self.device)
        model = bundle["model"]
        model.eval()
        with torch.no_grad():
            scaled_prediction = float(model(tensor).cpu().item())

        prediction = scaled_prediction * float(bundle["y_std"]) + float(bundle["y_mean"])
        if not np.isfinite(prediction) or prediction <= 0:
            return self._naive_projection(featured, fallback_price), 0.56, "naive"

        return float(prediction), 0.74, "lstm"

    def _load_model_bundle(self, symbol: str, timeframe: str) -> dict[str, Any] | None:
        cache_key = f"{symbol}:{timeframe}"
        if cache_key in self._bundle_cache:
            return self._bundle_cache[cache_key]

        model_path = self.saved_models_dir / f"{symbol}_{timeframe}.pt"
        if not model_path.exists():
            return None

        payload = torch.load(model_path, map_location=self.device)
        model = self._build_model(timeframe, input_size=int(payload["input_size"])).to(self.device)
        model.load_state_dict(payload["model_state"])
        payload["model"] = model
        self._bundle_cache[cache_key] = payload
        return payload

    def _build_model(self, timeframe: str, input_size: int):
        if timeframe in {"15m"}:
            return build_short_model(input_size)
        if timeframe in {"1d", "7d", "1month"}:
            return build_mid_model(input_size)
        return build_long_model(input_size)

    def _naive_projection(self, featured: pd.DataFrame, fallback_price: float) -> float:
        if featured.empty:
            return float(fallback_price)

        close = featured["close"].tail(40)
        ema = close.ewm(span=10, adjust=False).mean().iloc[-1]
        trend = (close.iloc[-1] - close.iloc[0]) / (close.iloc[0] + 1e-9)
        projected = float(fallback_price * (1 + trend * 0.6))
        blended = (projected * 0.7) + (float(ema) * 0.3)
        if not np.isfinite(blended) or blended <= 0:
            return float(fallback_price)
        return float(blended)
