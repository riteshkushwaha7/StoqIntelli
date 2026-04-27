from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from data.fetcher import MarketDataFetcher
from data.preprocessor import FeatureEngineer
from models.lstm_long import build_long_model
from models.lstm_mid import build_mid_model
from models.lstm_short import build_short_model

TIMEFRAME_FETCH_CONFIG: dict[str, dict[str, str]] = {
    # Keep within Yahoo's strict 60-day intraday limit.
    "15m": {"interval": "15m", "period": "60d"},
    "1d": {"interval": "1d", "period": "5y"},
    "7d": {"interval": "1d", "period": "10y"},
    "1month": {"interval": "1d", "period": "10y"},
    "1y": {"interval": "1d", "period": "10y"},
}

HORIZON_STEPS: dict[str, int] = {
    "15m": 2,
    "1d": 1,
    "7d": 7,
    "1month": 30,
    "1y": 252,
}

ALL_TIMEFRAMES = list(TIMEFRAME_FETCH_CONFIG.keys())


class LSTMTrainer:
    def __init__(
        self,
        saved_models_dir: str | Path = "saved_models",
        feature_engineer: FeatureEngineer | None = None,
        device: str | None = None,
    ) -> None:
        self.saved_models_dir = Path(saved_models_dir)
        self.saved_models_dir.mkdir(parents=True, exist_ok=True)
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    def train_symbol(
        self,
        symbol: str,
        fetcher: MarketDataFetcher,
        epochs: int = 16,
        lookback: int = 60,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        timeframes: list[str] | None = None,
    ) -> dict[str, Any]:
        chosen_timeframes = timeframes or ALL_TIMEFRAMES
        trained: list[dict[str, Any]] = []
        failed: list[dict[str, str]] = []

        for timeframe in chosen_timeframes:
            config = TIMEFRAME_FETCH_CONFIG.get(timeframe)
            if config is None:
                failed.append({"timeframe": timeframe, "reason": "Unsupported timeframe"})
                continue

            try:
                frame = fetcher.fetch_ohlcv(
                    symbol=symbol,
                    interval=config["interval"],
                    period=config["period"],
                )
                result = self.train_for_timeframe(
                    frame=frame,
                    timeframe=timeframe,
                    symbol=symbol.upper(),
                    epochs=epochs,
                    lookback=lookback,
                    batch_size=batch_size,
                    learning_rate=learning_rate,
                )
                trained.append(result)
            except Exception as exc:
                failed.append({"timeframe": timeframe, "reason": str(exc)})

        return {
            "symbol": symbol.upper(),
            "trained": trained,
            "failed": failed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def train_for_timeframe(
        self,
        frame: pd.DataFrame,
        timeframe: str,
        symbol: str,
        epochs: int,
        lookback: int,
        batch_size: int,
        learning_rate: float,
    ) -> dict[str, Any]:
        featured = self.feature_engineer.compute_features(frame)
        feature_columns = self.feature_engineer.get_feature_columns(featured)
        horizon = HORIZON_STEPS[timeframe]
        x_array, y_array = self.feature_engineer.to_sequences(
            data=featured,
            feature_columns=feature_columns,
            lookback=lookback,
            horizon=horizon,
        )

        if len(x_array) < 180:
            raise ValueError("Not enough candles after feature engineering to train model")

        split_index = int(len(x_array) * 0.8)
        x_train = x_array[:split_index]
        y_train = y_array[:split_index]
        x_val = x_array[split_index:]
        y_val = y_array[split_index:]

        x_train_scaled, x_val_scaled, x_mean, x_std = self._scale_features(x_train, x_val)
        y_train_scaled, y_val_scaled, y_mean, y_std = self._scale_target(y_train, y_val)

        train_loader = DataLoader(
            TensorDataset(
                torch.tensor(x_train_scaled, dtype=torch.float32),
                torch.tensor(y_train_scaled, dtype=torch.float32),
            ),
            batch_size=batch_size,
            shuffle=True,
        )
        val_loader = DataLoader(
            TensorDataset(
                torch.tensor(x_val_scaled, dtype=torch.float32),
                torch.tensor(y_val_scaled, dtype=torch.float32),
            ),
            batch_size=batch_size,
            shuffle=False,
        )

        model = self._build_model(timeframe, input_size=len(feature_columns)).to(self.device)
        optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()

        best_val_loss = float("inf")
        best_state = deepcopy(model.state_dict())
        patience = 4
        wait = 0
        last_train_loss = 0.0
        last_val_loss = 0.0

        for _ in range(epochs):
            model.train()
            train_losses: list[float] = []
            for batch_x, batch_y in train_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)
                optimizer.zero_grad()
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_losses.append(float(loss.item()))

            model.eval()
            val_losses: list[float] = []
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    batch_x = batch_x.to(self.device)
                    batch_y = batch_y.to(self.device)
                    outputs = model(batch_x)
                    val_loss = criterion(outputs, batch_y)
                    val_losses.append(float(val_loss.item()))

            last_train_loss = float(np.mean(train_losses)) if train_losses else last_train_loss
            last_val_loss = float(np.mean(val_losses)) if val_losses else last_val_loss
            if last_val_loss < best_val_loss:
                best_val_loss = last_val_loss
                best_state = deepcopy(model.state_dict())
                wait = 0
            else:
                wait += 1
                if wait >= patience:
                    break

        model.load_state_dict(best_state)
        model_path = self.saved_models_dir / f"{symbol}_{timeframe}.pt"
        torch.save(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "lookback": lookback,
                "horizon": horizon,
                "input_size": len(feature_columns),
                "feature_columns": feature_columns,
                "x_mean": x_mean.tolist(),
                "x_std": x_std.tolist(),
                "y_mean": float(y_mean),
                "y_std": float(y_std),
                "model_state": model.state_dict(),
                "trained_at": datetime.now(timezone.utc).isoformat(),
            },
            model_path,
        )

        return {
            "timeframe": timeframe,
            "samples": int(len(x_array)),
            "train_loss": round(last_train_loss, 6),
            "val_loss": round(best_val_loss, 6),
            "model_path": str(model_path),
        }

    def _build_model(self, timeframe: str, input_size: int):
        if timeframe in {"15m"}:
            return build_short_model(input_size=input_size)
        if timeframe in {"1d", "7d", "1month"}:
            return build_mid_model(input_size=input_size)
        return build_long_model(input_size=input_size)

    @staticmethod
    def _scale_features(
        x_train: np.ndarray, x_val: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        x_mean = x_train.mean(axis=(0, 1))
        x_std = x_train.std(axis=(0, 1)) + 1e-8
        x_train_scaled = (x_train - x_mean) / x_std
        x_val_scaled = (x_val - x_mean) / x_std
        return x_train_scaled, x_val_scaled, x_mean.astype(np.float32), x_std.astype(np.float32)

    @staticmethod
    def _scale_target(
        y_train: np.ndarray, y_val: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, float, float]:
        y_mean = float(np.mean(y_train))
        y_std = float(np.std(y_train) + 1e-8)
        y_train_scaled = (y_train - y_mean) / y_std
        y_val_scaled = (y_val - y_mean) / y_std
        return y_train_scaled, y_val_scaled, y_mean, y_std
