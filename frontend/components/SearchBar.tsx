"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

const AVAILABLE_TIMEFRAMES = ["15m", "1d", "7d", "1month", "1y"] as const;

type SearchBarProps = {
  defaultValue?: string;
  defaultTimeframes?: string[];
  compact?: boolean;
};

function normalizeSelection(input: string[] | undefined): string[] {
  if (!input || input.length === 0) {
    return [...AVAILABLE_TIMEFRAMES];
  }
  const set = new Set(input);
  const normalized = AVAILABLE_TIMEFRAMES.filter((timeframe) => set.has(timeframe));
  return normalized.length > 0 ? normalized : [...AVAILABLE_TIMEFRAMES];
}

export default function SearchBar({
  defaultValue = "",
  defaultTimeframes = [...AVAILABLE_TIMEFRAMES],
  compact = false
}: SearchBarProps) {
  const [symbol, setSymbol] = useState(defaultValue);
  const [selectedTimeframes, setSelectedTimeframes] = useState<string[]>(normalizeSelection(defaultTimeframes));
  const router = useRouter();

  useEffect(() => {
    setSymbol(defaultValue);
  }, [defaultValue]);

  useEffect(() => {
    setSelectedTimeframes(normalizeSelection(defaultTimeframes));
  }, [defaultTimeframes]);

  const allSelected = useMemo(
    () => selectedTimeframes.length === AVAILABLE_TIMEFRAMES.length,
    [selectedTimeframes]
  );

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const clean = symbol.trim().toUpperCase();
    if (!clean) return;
    const query = new URLSearchParams();
    if (selectedTimeframes.length > 0) {
      query.set("timeframes", selectedTimeframes.join(","));
    }
    const search = query.toString();
    router.push(`/stock/${encodeURIComponent(clean)}${search ? `?${search}` : ""}`);
  };

  const toggleTimeframe = (timeframe: string) => {
    if (selectedTimeframes.includes(timeframe)) {
      const next = selectedTimeframes.filter((item) => item !== timeframe);
      setSelectedTimeframes(next.length === 0 ? [timeframe] : next);
      return;
    }
    const nextSet = new Set([...selectedTimeframes, timeframe]);
    setSelectedTimeframes(AVAILABLE_TIMEFRAMES.filter((item) => nextSet.has(item)));
  };

  const toggleAll = () => {
    setSelectedTimeframes(allSelected ? ["1d"] : [...AVAILABLE_TIMEFRAMES]);
  };

  return (
    <form onSubmit={onSubmit} style={compact ? { maxWidth: 760 } : undefined}>
      <div className="search-row">
        <input
          className="search-input"
          value={symbol}
          placeholder="Search NSE symbol (e.g., RELIANCE, TCS, INFY)"
          onChange={(event) => setSymbol(event.target.value)}
        />
        <button className="search-button" type="submit" disabled={!symbol.trim()}>
          Analyze
        </button>
      </div>

      <div className="timeframe-inline">
        <span className="timeframe-label">Timeframes:</span>
        <label className="timeframe-option-inline">
          <input type="checkbox" checked={allSelected} onChange={toggleAll} />
          <span>All</span>
        </label>
        {AVAILABLE_TIMEFRAMES.map((timeframe) => (
          <label className="timeframe-option-inline" key={timeframe}>
            <input
              type="checkbox"
              checked={selectedTimeframes.includes(timeframe)}
              onChange={() => toggleTimeframe(timeframe)}
            />
            <span>{timeframe}</span>
          </label>
        ))}
      </div>
    </form>
  );
}
