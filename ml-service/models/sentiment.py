from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any

import feedparser

from data.cache import HybridCache
from data.fetcher import MarketDataFetcher


@dataclass
class SentimentResult:
    score: float
    label: str
    confidence: float
    articles_considered: int
    headlines: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SentimentAnalyzer:
    """Financial sentiment scoring with FinBERT (when available) + lexical fallback."""

    POSITIVE_WORDS = {
        "beat",
        "beats",
        "bull",
        "bullish",
        "buy",
        "growth",
        "upside",
        "upgrade",
        "surge",
        "rally",
        "profit",
        "gains",
        "strong",
    }
    NEGATIVE_WORDS = {
        "miss",
        "bear",
        "bearish",
        "sell",
        "downgrade",
        "fraud",
        "lawsuit",
        "plunge",
        "drop",
        "weak",
        "loss",
        "decline",
        "risk",
    }

    def __init__(
        self,
        fetcher: MarketDataFetcher,
        cache: HybridCache | None = None,
        model_name: str = "ProsusAI/finbert",
    ) -> None:
        self.fetcher = fetcher
        self.cache = cache
        self.model_name = model_name
        self._pipeline = None
        self._pipeline_failed = False

    def score(self, symbol: str, max_items: int = 10) -> SentimentResult:
        cache_key = f"sentiment:{symbol.upper()}:{max_items}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return SentimentResult(**cached)

        headlines = self._fetch_headlines(symbol, max_items=max_items)
        if not headlines:
            result = SentimentResult(
                score=0.0,
                label="neutral",
                confidence=0.4,
                articles_considered=0,
                headlines=[],
            )
            if self.cache:
                self.cache.set(cache_key, result.to_dict(), ttl_seconds=300)
            return result

        sentiment_scores = self._finbert_scores(headlines)
        if not sentiment_scores:
            sentiment_scores = [self._lexical_score(text) for text in headlines]

        final_score = max(-1.0, min(1.0, mean(sentiment_scores)))
        if final_score >= 0.12:
            label = "bullish"
        elif final_score <= -0.12:
            label = "bearish"
        else:
            label = "neutral"

        confidence = max(0.35, min(0.98, 0.45 + abs(final_score)))
        result = SentimentResult(
            score=round(final_score, 6),
            label=label,
            confidence=round(confidence, 6),
            articles_considered=len(headlines),
            headlines=headlines,
        )

        if self.cache:
            self.cache.set(cache_key, result.to_dict(), ttl_seconds=300)
        return result

    def _fetch_headlines(self, symbol: str, max_items: int) -> list[str]:
        feed_url = self.fetcher.fetch_news_rss_url(symbol)
        parsed = feedparser.parse(feed_url)
        titles: list[str] = []
        for entry in parsed.entries[:max_items]:
            title = str(entry.get("title", "")).strip()
            if title:
                titles.append(title)
        return titles

    def _finbert_scores(self, texts: list[str]) -> list[float]:
        pipeline_instance = self._get_pipeline()
        if pipeline_instance is None:
            return []

        scores: list[float] = []
        try:
            for item in texts:
                result = pipeline_instance(item, truncation=True, max_length=256)[0]
                label = str(result.get("label", "")).lower()
                confidence = float(result.get("score", 0.0))
                if "positive" in label:
                    scores.append(confidence)
                elif "negative" in label:
                    scores.append(-confidence)
                else:
                    scores.append(0.0)
        except Exception:
            return []

        return scores

    def _get_pipeline(self):
        if self._pipeline_failed:
            return None
        if self._pipeline is not None:
            return self._pipeline
        try:
            from transformers import pipeline

            self._pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
            )
        except Exception:
            self._pipeline_failed = True
            return None
        return self._pipeline

    def _lexical_score(self, text: str) -> float:
        lowered_tokens = text.lower().replace(",", " ").replace(".", " ").split()
        if not lowered_tokens:
            return 0.0
        positive_hits = sum(1 for token in lowered_tokens if token in self.POSITIVE_WORDS)
        negative_hits = sum(1 for token in lowered_tokens if token in self.NEGATIVE_WORDS)
        score = (positive_hits - negative_hits) / max(1, len(lowered_tokens) // 3)
        return float(max(-1.0, min(1.0, score)))

