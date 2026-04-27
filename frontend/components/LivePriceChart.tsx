"use client";

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { Candle } from "@/lib/api";

type PriceChartPoint = {
  timestamp: string;
  close: number;
  high: number;
  low: number;
};

type LivePriceChartProps = {
  candles: Candle[];
};

function formatTimeLabel(isoDate: string) {
  const date = new Date(isoDate);
  if (Number.isNaN(date.getTime())) return isoDate;
  return `${date.toLocaleDateString("en-IN", {
    month: "short",
    day: "numeric"
  })} ${date.toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit"
  })}`;
}

export default function LivePriceChart({ candles }: LivePriceChartProps) {
  const chartData: PriceChartPoint[] = candles.slice(-100).map((item) => ({
    timestamp: formatTimeLabel(String(item.timestamp)),
    close: Number(item.close),
    high: Number(item.high),
    low: Number(item.low)
  }));

  if (chartData.length === 0) {
    return <div className="card">No price data available.</div>;
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0, marginBottom: 14 }}>Live Price Trend</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 8, left: 8, bottom: 4 }}>
            <CartesianGrid stroke="#e5e7eb" strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" minTickGap={30} stroke="#6b7280" />
            <YAxis
              domain={["dataMin - 2", "dataMax + 2"]}
              tickFormatter={(value) => `Rs ${Number(value).toFixed(0)}`}
              width={72}
              stroke="#6b7280"
            />
            <Tooltip
              formatter={(value: number, _name, context) => {
                const payload = context?.payload as PriceChartPoint | undefined;
                if (!payload) return [value, "Price"];
                return [
                  `Close ${payload.close.toFixed(2)} | High ${payload.high.toFixed(
                    2
                  )} | Low ${payload.low.toFixed(2)}`,
                  "Price"
                ];
              }}
              labelFormatter={(label) => `Time: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="close"
              stroke="#1d4ed8"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

