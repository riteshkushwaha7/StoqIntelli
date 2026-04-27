from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd


class FeatureEngineer:
    BASE_FEATURE_COLUMNS = [
        "close",
        "volume",
        "return_1",
        "return_3",
        "ema_12",
        "ema_26",
        "ema_spread",
        "macd",
        "macd_signal",
        "macd_hist",
        "rsi_14",
        "bb_middle",
        "bb_upper",
        "bb_lower",
        "bb_width",
        "candle_body",
        "upper_wick",
        "lower_wick",
        "candle_direction",
        "volume_zscore",
    ]

    def compute_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return frame.copy()

        data = frame.copy()
        data = data.sort_index()
        close = data["close"]
        volume = data["volume"]

        data["return_1"] = close.pct_change()
        data["return_3"] = close.pct_change(periods=3)

        data["ema_12"] = close.ewm(span=12, adjust=False).mean()
        data["ema_26"] = close.ewm(span=26, adjust=False).mean()
        data["ema_spread"] = data["ema_12"] - data["ema_26"]

        data["macd"] = data["ema_spread"]
        data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
        data["macd_hist"] = data["macd"] - data["macd_signal"]

        delta = close.diff()
        gains = delta.clip(lower=0.0)
        losses = -delta.clip(upper=0.0)
        avg_gain = gains.rolling(window=14, min_periods=14).mean()
        avg_loss = losses.rolling(window=14, min_periods=14).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        data["rsi_14"] = 100 - (100 / (1 + rs))

        data["bb_middle"] = close.rolling(window=20, min_periods=20).mean()
        bb_std = close.rolling(window=20, min_periods=20).std()
        data["bb_upper"] = data["bb_middle"] + (2 * bb_std)
        data["bb_lower"] = data["bb_middle"] - (2 * bb_std)
        data["bb_width"] = (data["bb_upper"] - data["bb_lower"]) / (data["bb_middle"] + 1e-9)

        data["candle_body"] = (data["close"] - data["open"]).abs()
        data["upper_wick"] = data["high"] - data[["open", "close"]].max(axis=1)
        data["lower_wick"] = data[["open", "close"]].min(axis=1) - data["low"]
        data["candle_direction"] = np.where(data["close"] >= data["open"], 1.0, -1.0)

        rolling_volume_mean = volume.rolling(window=20, min_periods=20).mean()
        rolling_volume_std = volume.rolling(window=20, min_periods=20).std() + 1e-9
        data["volume_zscore"] = (volume - rolling_volume_mean) / rolling_volume_std

        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        return data

    def get_feature_columns(self, data: pd.DataFrame | None = None) -> list[str]:
        if data is None:
            return self.BASE_FEATURE_COLUMNS.copy()
        return [column for column in self.BASE_FEATURE_COLUMNS if column in data.columns]

    def to_sequences(
        self,
        data: pd.DataFrame,
        feature_columns: Sequence[str],
        target_column: str = "close",
        lookback: int = 60,
        horizon: int = 1,
    ) -> tuple[np.ndarray, np.ndarray]:
        if len(data) <= lookback + horizon:
            return np.array([]), np.array([])

        features = data[list(feature_columns)].to_numpy(dtype=np.float32)
        target = data[target_column].to_numpy(dtype=np.float32)

        x_values: list[np.ndarray] = []
        y_values: list[float] = []
        max_end = len(data) - horizon + 1
        for end in range(lookback, max_end):
            start = end - lookback
            x_values.append(features[start:end])
            y_values.append(target[end + horizon - 1])

        return np.asarray(x_values, dtype=np.float32), np.asarray(y_values, dtype=np.float32)

    def latest_sequence(
        self,
        data: pd.DataFrame,
        feature_columns: Sequence[str],
        lookback: int = 60,
    ) -> np.ndarray | None:
        if len(data) < lookback:
            return None
        sequence = data[list(feature_columns)].tail(lookback).to_numpy(dtype=np.float32)
        return sequence

