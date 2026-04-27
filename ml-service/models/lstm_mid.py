from __future__ import annotations

import torch
from torch import nn


class MidHorizonLSTM(nn.Module):
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 96,
        num_layers: int = 2,
        dropout: float = 0.25,
    ) -> None:
        super().__init__()
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=lstm_dropout,
            batch_first=True,
        )
        self.regressor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        outputs, _ = self.lstm(inputs)
        features = outputs[:, -1, :]
        return self.regressor(features).squeeze(-1)


def build_mid_model(input_size: int) -> MidHorizonLSTM:
    return MidHorizonLSTM(input_size=input_size)

