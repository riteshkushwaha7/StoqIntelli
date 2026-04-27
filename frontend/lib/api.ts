export type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  [key: string]: number | string;
};

export type StockQuote = {
  source?: string;
  price: number;
  change: number;
  change_percent: number;
  volume?: number;
  timestamp: string;
};

export type StockResponse = {
  symbol: string;
  interval: string;
  period: string;
  quote: StockQuote;
  candles: Candle[];
};

export type PredictionPoint = {
  predicted_price: number;
  direction: "up" | "down" | "flat";
  confidence: number;
  price_change_pct: number;
  price_source: string;
  sentiment_adjustment: number;
};

export type SentimentResponse = {
  score: number;
  label: "bullish" | "bearish" | "neutral";
  confidence: number;
  articles_considered: number;
  headlines: string[];
};

export type PredictionResponse = {
  symbol: string;
  current_price: number;
  timestamp: string;
  sentiment: SentimentResponse;
  predictions: Record<string, PredictionPoint>;
};

const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_ML_SERVICE_URL ?? "http://127.0.0.1:8000";

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep default detail.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export async function fetchStockData(symbol: string): Promise<StockResponse> {
  return fetchJson<StockResponse>(`${BACKEND_BASE_URL}/stock/${encodeURIComponent(symbol)}`);
}

export async function fetchPredictions(symbol: string, timeframes?: string[]): Promise<PredictionResponse> {
  const params = new URLSearchParams();
  if (timeframes && timeframes.length > 0) {
    params.set("timeframes", timeframes.join(","));
  }
  const query = params.toString();
  const url = `${BACKEND_BASE_URL}/predict/${encodeURIComponent(symbol)}${query ? `?${query}` : ""}`;
  return fetchJson<PredictionResponse>(url);
}
