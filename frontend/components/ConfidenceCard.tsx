import type { PredictionPoint } from "@/lib/api";

type ConfidenceCardProps = {
  timeframe: string;
  prediction: PredictionPoint;
};

function toneClass(direction: PredictionPoint["direction"]) {
  if (direction === "up") return "pill pill-up";
  if (direction === "down") return "pill pill-down";
  return "pill pill-flat";
}

export default function ConfidenceCard({ timeframe, prediction }: ConfidenceCardProps) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h4 style={{ margin: 0 }}>{timeframe}</h4>
        <span className={toneClass(prediction.direction)}>{prediction.direction.toUpperCase()}</span>
      </div>
      <p className="metric-title">Confidence</p>
      <p className="metric-value">{prediction.confidence.toFixed(1)}%</p>
      <p className="metric-title" style={{ marginTop: 10 }}>
        Model Source
      </p>
      <strong style={{ textTransform: "uppercase" }}>{prediction.price_source}</strong>
    </div>
  );
}

