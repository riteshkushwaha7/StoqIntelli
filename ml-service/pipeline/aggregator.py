from __future__ import annotations

from typing import Any


class EnsembleAggregator:
    """Combines price model output with sentiment signal."""

    def __init__(
        self,
        price_weight: float = 0.7,
        sentiment_weight: float = 0.3,
        max_sentiment_impact: float = 0.03,
    ) -> None:
        self.price_weight = price_weight
        self.sentiment_weight = sentiment_weight
        self.max_sentiment_impact = max_sentiment_impact

    def combine_predictions(
        self,
        current_price: float,
        price_predictions: dict[str, dict[str, Any]],
        sentiment: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        sentiment_score = float(sentiment.get("score", 0.0))
        final_predictions: dict[str, dict[str, Any]] = {}
        for timeframe, payload in price_predictions.items():
            model_price = float(payload["predicted_price"])
            base_confidence = float(payload.get("confidence", 0.6))
            final_price, direction, confidence, change_pct, sentiment_adjustment = self.combine_single(
                current_price=current_price,
                model_price=model_price,
                sentiment_score=sentiment_score,
                base_confidence=base_confidence,
            )
            final_predictions[timeframe] = {
                "predicted_price": round(final_price, 4),
                "direction": direction,
                "confidence": round(confidence * 100.0, 2),
                "price_change_pct": round(change_pct, 4),
                "price_source": payload.get("source", "naive"),
                "sentiment_adjustment": round(sentiment_adjustment, 6),
            }
        return final_predictions

    def combine_single(
        self,
        current_price: float,
        model_price: float,
        sentiment_score: float,
        base_confidence: float,
    ) -> tuple[float, str, float, float, float]:
        model_move = (model_price - current_price) / (current_price + 1e-9)
        sentiment_move = sentiment_score * self.max_sentiment_impact
        blended_move = (model_move * self.price_weight) + (sentiment_move * self.sentiment_weight)
        final_price = current_price * (1 + blended_move)

        if blended_move > 0.0015:
            direction = "up"
        elif blended_move < -0.0015:
            direction = "down"
        else:
            direction = "flat"

        confidence_boost = min(0.18, abs(sentiment_score) * self.sentiment_weight * 0.6)
        confidence = max(0.35, min(0.98, base_confidence + confidence_boost))
        change_pct = ((final_price - current_price) / (current_price + 1e-9)) * 100.0
        return final_price, direction, confidence, change_pct, sentiment_move

