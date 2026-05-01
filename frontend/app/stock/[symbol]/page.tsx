"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import ConfidenceCard from "@/components/ConfidenceCard";
import LivePriceChart from "@/components/LivePriceChart";
import PredictionTimeline from "@/components/PredictionTimeline";
import SearchBar from "@/components/SearchBar";
import TimeframeSelector from "@/components/TimeframeSelector";
import { fetchPredictions, fetchStockData, type PredictionPoint, type PredictionResponse, type StockResponse } from "@/lib/api";

const DEFAULT_TIMEFRAMES = ["15m", "1d", "7d", "1month", "1y"];

export default function StockDashboardPage() {
  const params = useParams<{ symbol: string }>();
  const symbol = useMemo(() => String(params?.symbol || "").toUpperCase(), [params]);
  const [stock, setStock] = useState<StockResponse | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [stockError, setStockError] = useState<string | null>(null);
  const [predictionError, setPredictionError] = useState<string | null>(null);
  const [stockLoading, setStockLoading] = useState(true);
  const [predictionLoading, setPredictionLoading] = useState(true);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(DEFAULT_TIMEFRAMES);

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
    if (!symbol) return;
    if (selectedTimeframes.length === 0) {
      setPredictionLoading(false);
      setPredictionError(null);
      setPrediction(null);
      return;
    }
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
        <SearchBar defaultValue={symbol} compact />
        <div className="card" style={{ marginTop: 12 }}>
          Loading {symbol} dashboard...
        </div>
      </main>
    );
  }

  if (stockError || !stock) {
    return (
      <main className="page-shell">
        <SearchBar defaultValue={symbol} compact />
        <div className="card" style={{ marginTop: 12 }}>
          Failed to load data for {symbol}. {stockError ?? "Please try again."}
        </div>
      </main>
    );
  }

  const quote = stock.quote || {};
  const price = typeof quote.price === "number" ? quote.price : 0;
  const change = typeof quote.change === "number" ? quote.change : 0;
  const changePercent = typeof quote.change_percent === "number" ? quote.change_percent : 0;
  const quoteDirectionClass =
    change > 0 ? "pill pill-up" : change < 0 ? "pill pill-down" : "pill pill-flat";

  const predictionEntries = prediction
    ? Object.entries(prediction.predictions).filter(([timeframe]) => selectedTimeframes.includes(timeframe))
    : [];
  const filteredPredictions = predictionEntries.reduce<Record<string, PredictionPoint>>((acc, [timeframe, point]) => {
    acc[timeframe] = point;
    return acc;
  }, {});
  const strongestTimeframe = predictionEntries.sort((a, b) => b[1].confidence - a[1].confidence)[0];
  const lastComputed = prediction?.timestamp ? new Date(prediction.timestamp).toLocaleString() : null;

  return (
    <main className="page-shell">
      <section className="hero">
        <SearchBar defaultValue={symbol} compact />
        <div className="status-row">
          <p className="status-pill">{selectedTimeframes.length} timeframe(s) selected</p>
          <p className="status-muted">{lastComputed ? `Last computed at ${lastComputed}` : "Awaiting computation"}</p>
        </div>
        <div className="grid" style={{ marginTop: 16 }}>
          <article className="card" style={{ gridColumn: "span 6" }}>
            <p className="metric-title">{symbol} Current Price</p>
            <p className="metric-value">Rs {price.toFixed(2)}</p>
            <span className={quoteDirectionClass}>
              {change >= 0 ? "+" : ""}
              {change.toFixed(2)} ({changePercent.toFixed(2)}%)
            </span>
          </article>
          <article className="card" style={{ gridColumn: "span 6" }}>
            <p className="metric-title">Strongest Signal</p>
            <p className="metric-value">{strongestTimeframe?.[0] ?? "-"}</p>
            <span className="pill pill-flat">
              {strongestTimeframe ? `${strongestTimeframe[1].confidence.toFixed(1)}% confidence` : "No signal"}
            </span>
          </article>
        </div>
      </section>

      <section className="grid" style={{ marginTop: 16 }}>
        <div style={{ gridColumn: "span 12" }}>
          <div className="card">
            <TimeframeSelector selected={selectedTimeframes} onChange={setSelectedTimeframes} />
          </div>
        </div>
      </section>

      {predictionError && (
        <section className="grid" style={{ marginTop: 16 }}>
          <div className="card" style={{ gridColumn: "span 12" }}>
            Prediction error: {predictionError}
          </div>
        </section>
      )}

      <section className="grid" style={{ marginTop: 16 }}>
        <div style={{ gridColumn: "span 12" }}>
          <LivePriceChart candles={stock.candles} />
        </div>
      </section>

      {prediction && predictionEntries.length > 0 && (
        <section className="grid" style={{ marginTop: 16 }}>
          <div style={{ gridColumn: "span 8" }}>
            <PredictionTimeline predictions={filteredPredictions} />
          </div>
          <div style={{ gridColumn: "span 4", display: "grid", gap: 12 }}>
            {Object.entries(filteredPredictions).map(([timeframe, point]) => (
              <ConfidenceCard key={timeframe} timeframe={timeframe} prediction={point} />
            ))}
          </div>
        </section>
      )}

      {selectedTimeframes.length === 0 && (
        <section className="grid" style={{ marginTop: 16 }}>
          <div className="card" style={{ gridColumn: "span 12" }}>
            Select at least one timeframe above to trigger computation.
          </div>
        </section>
      )}

      {prediction && selectedTimeframes.length > 0 && predictionEntries.length === 0 && (
        <section className="grid" style={{ marginTop: 16 }}>
          <div className="card" style={{ gridColumn: "span 12" }}>
            No predictions returned yet for the selected timeframes. Try refreshing or running training.
          </div>
        </section>
      )}
    </main>
  );
}
