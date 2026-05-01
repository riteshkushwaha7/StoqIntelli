from __future__ import annotations

from typing import Any


class EnsembleAggregator:
    """Formats raw price predictions into consistent output."""

    def format_predictions(
        self,
        current_price: float,
        price_predictions: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        final_predictions: dict[str, dict[str, Any]] = {}
        for timeframe, payload in price_predictions.items():
            model_price = float(payload["predicted_price"])
            base_confidence = float(payload.get("confidence", 0.6))
            final_price, direction, confidence, change_pct = self._format_single(
                current_price=current_price,
                model_price=model_price,
                base_confidence=base_confidence,
            )
            final_predictions[timeframe] = {
                "predicted_price": round(final_price, 4),
                "direction": direction,
                "confidence": round(confidence * 100.0, 2),
                "price_change_pct": round(change_pct, 4),
                "price_source": payload.get("source", "naive"),
            }
        return final_predictions

    def _format_single(
        self,
        current_price: float,
        model_price: float,
        base_confidence: float,
    ) -> tuple[float, str, float, float]:
        move = (model_price - current_price) / (current_price + 1e-9)
        final_price = model_price

        if move > 0.0015:
            direction = "up"
        elif move < -0.0015:
            direction = "down"
        else:
            direction = "flat"

        confidence = max(0.35, min(0.98, base_confidence))
        change_pct = move * 100.0
        return final_price, direction, confidence, change_pct

