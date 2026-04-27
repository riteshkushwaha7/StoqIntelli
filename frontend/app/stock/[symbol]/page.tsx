"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

import ConfidenceCard from "@/components/ConfidenceCard";
import LivePriceChart from "@/components/LivePriceChart";
import PredictionTimeline from "@/components/PredictionTimeline";
import SearchBar from "@/components/SearchBar";
import SentimentGauge from "@/components/SentimentGauge";
import { fetchPredictions, fetchStockData, type PredictionResponse, type StockResponse } from "@/lib/api";

const DEFAULT_TIMEFRAMES = ["15m", "1d", "7d", "1month", "1y"];
const CONFIDENCE_OVERVIEW_TIMEFRAMES = ["15m", "1d", "1y"];

export default function StockDashboardPage() {
  const params = useParams<{ symbol: string }>();
  const searchParams = useSearchParams();
  const symbol = useMemo(() => String(params?.symbol || "").toUpperCase(), [params]);
  const selectedTimeframes = useMemo(() => {
    const param = searchParams.get("timeframes");
    if (!param) return DEFAULT_TIMEFRAMES;
    const parsed = param
      .split(",")
      .map((item) => item.trim())
      .filter((item) => DEFAULT_TIMEFRAMES.includes(item));
    return parsed.length > 0 ? parsed : DEFAULT_TIMEFRAMES;
  }, [searchParams]);
  const [stock, setStock] = useState<StockResponse | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [stockError, setStockError] = useState<string | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [stockLoading, setStockLoading] = useState(true);
  const [predictionLoading, setPredictionLoading] = useState(true);

  useEffect(() => {
    if (!symbol) return;
    let mounted = true;
    setStockLoading(true);
    setStockError(null);

    fetchStockData(symbol)
      .then((stockData) => {
        if (!mounted) return;
        setStock(stockData);
      })
      .catch((reason) => {
        if (!mounted) return;
        setStockError(reason instanceof Error ? reason.message : "Unable to load stock data");
      })
      .finally(() => {
        if (!mounted) return;
        setStockLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [symbol]);

  useEffect(() => {
    if (!symbol || selectedTimeframes.length === 0) return;
    let mounted = true;
    setPredictionLoading(true);
    setPredictionError(null);

    fetchPredictions(symbol, selectedTimeframes)
      .then((predictionData) => {
        if (!mounted) return;
        setPrediction(predictionData);
      })
      .catch((reason) => {
        if (!mounted) return;
        setPredictionError(reason instanceof Error ? reason.message : "Unable to load predictions");
      })
      .finally(() => {
        if (!mounted) return;
        setPredictionLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [symbol, selectedTimeframes]);

  if (!symbol) {
    return (
      <main className="page-shell">
        <div className="card">Invalid symbol.</div>
      </main>
    );
  }

  if (stockLoading || predictionLoading) {
    return (
      <main className="page-shell">
        <SearchBar defaultValue={symbol} defaultTimeframes={selectedTimeframes} compact />
        <div className="card" style={{ marginTop: 12 }}>
          Loading {symbol} dashboard...
        </div>
      </main>
    );
  }

  if (stockError || !stock) {
    return (
      <main className="page-shell">
        <SearchBar defaultValue={symbol} defaultTimeframes={selectedTimeframes} compact />
        <div className="card" style={{ marginTop: 12 }}>
          Failed to load data for {symbol}. {stockError ?? "Please try again."}
        </div>
      </main>
    );
  }

  if (predictionError || !prediction) {
    return (
      <main className="page-shell">
        <SearchBar defaultValue={symbol} defaultTimeframes={selectedTimeframes} compact />
        <div className="card" style={{ marginTop: 12 }}>
          Failed to load predictions for {symbol}. {predictionError ?? "Please try again."}
        </div>
      </main>
    );
  }

  const quote = stock.quote;
  const quoteDirectionClass =
    quote.change > 0 ? "pill pill-up" : quote.change < 0 ? "pill pill-down" : "pill pill-flat";
  const strongestTimeframe = Object.entries(prediction.predictions).sort(
    (a, b) => b[1].confidence - a[1].confidence
  )[0];

  return (
    <main className="page-shell">
      <section className="hero">
        <SearchBar defaultValue={symbol} defaultTimeframes={selectedTimeframes} compact />
        <div className="grid" style={{ marginTop: 16 }}>
          <article className="card" style={{ gridColumn: "span 4" }}>
            <p className="metric-title">{symbol} Current Price</p>
            <p className="metric-value">Rs {quote.price.toFixed(2)}</p>
            <span className={quoteDirectionClass}>
              {quote.change >= 0 ? "+" : ""}
              {quote.change.toFixed(2)} ({quote.change_percent.toFixed(2)}%)
            </span>
          </article>
          <article className="card" style={{ gridColumn: "span 4" }}>
            <p className="metric-title">Strongest Signal</p>
            <p className="metric-value">{strongestTimeframe?.[0] ?? "-"}</p>
            <span className="pill pill-flat">
              {strongestTimeframe ? `${strongestTimeframe[1].confidence.toFixed(1)}% confidence` : "No signal"}
            </span>
          </article>
          <article className="card" style={{ gridColumn: "span 4" }}>
            <p className="metric-title">Sentiment Direction</p>
            <p className="metric-value" style={{ textTransform: "capitalize" }}>
              {prediction.sentiment.label}
            </p>
            <span className={quoteDirectionClass}>{prediction.sentiment.articles_considered} news articles</span>
          </article>
        </div>
      </section>

      <section className="grid" style={{ marginTop: 16 }}>
        <div style={{ gridColumn: "span 8" }}>
          <LivePriceChart candles={stock.candles} />
        </div>
        <div style={{ gridColumn: "span 4", display: "grid", gap: 12 }}>
          <SentimentGauge sentiment={prediction.sentiment} />
        </div>
      </section>

      <section className="grid" style={{ marginTop: 16 }}>
        <div style={{ gridColumn: "span 8" }}>
          <PredictionTimeline predictions={prediction.predictions} />
        </div>
        <div style={{ gridColumn: "span 4", display: "grid", gap: 12 }}>
          {CONFIDENCE_OVERVIEW_TIMEFRAMES.filter((timeframe) => prediction.predictions[timeframe]).map(
            (timeframe) => (
              <ConfidenceCard key={timeframe} timeframe={timeframe} prediction={prediction.predictions[timeframe]} />
            )
          )}
        </div>
      </section>
    </main>
  );
}
