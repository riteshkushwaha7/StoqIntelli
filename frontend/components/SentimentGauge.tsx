import type { SentimentResponse } from "@/lib/api";

type SentimentGaugeProps = {
  sentiment: SentimentResponse;
};

function labelStyle(label: SentimentResponse["label"]) {
  if (label === "bullish") return "pill pill-up";
  if (label === "bearish") return "pill pill-down";
  return "pill pill-flat";
}

export default function SentimentGauge({ sentiment }: SentimentGaugeProps) {
  const markerLeft = ((sentiment.score + 1) / 2) * 100;
  return (
    <div className="card">
      <h3 style={{ marginTop: 0, marginBottom: 12 }}>Sentiment Meter</h3>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
        <span className={labelStyle(sentiment.label)}>{sentiment.label.toUpperCase()}</span>
        <strong>{(sentiment.confidence * 100).toFixed(1)}% confidence</strong>
      </div>
      <div className="gauge-track">
        <div className="gauge-marker" style={{ left: `${markerLeft}%` }} />
      </div>
      <p className="subtitle" style={{ marginBottom: 0, marginTop: 10 }}>
        Score: {sentiment.score.toFixed(3)} across {sentiment.articles_considered} news headlines.
      </p>
      {sentiment.headlines.length > 0 ? (
        <ul className="headline-list">
          {sentiment.headlines.slice(0, 3).map((headline) => (
            <li key={headline}>{headline}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

