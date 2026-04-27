import type { PredictionPoint } from "@/lib/api";

const TIMEFRAME_ORDER = ["15m", "1d", "7d", "1month", "1y"];

type PredictionTimelineProps = {
  predictions: Record<string, PredictionPoint>;
};

function badgeClass(direction: PredictionPoint["direction"]) {
  if (direction === "up") return "pill pill-up";
  if (direction === "down") return "pill pill-down";
  return "pill pill-flat";
}

export default function PredictionTimeline({ predictions }: PredictionTimelineProps) {
  const ordered = TIMEFRAME_ORDER.filter((timeframe) => predictions[timeframe]).map((timeframe) => ({
    timeframe,
    point: predictions[timeframe]
  }));

  return (
    <div className="card">
      <h3 style={{ marginTop: 0, marginBottom: 14 }}>Prediction Timeline</h3>
      <ul className="timeline-list">
        {ordered.map(({ timeframe, point }) => (
          <li className="timeline-item" key={timeframe}>
            <div className="timeline-top">
              <h4>{timeframe}</h4>
              <span className={badgeClass(point.direction)}>{point.direction.toUpperCase()}</span>
            </div>
            <div className="timeline-meta">
              Target: Rs {point.predicted_price.toFixed(2)} | Change: {point.price_change_pct.toFixed(2)}% |
              Confidence: {point.confidence.toFixed(1)}%
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
