"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { SUPPORTED_SYMBOLS, getSupportedSymbol } from "@/lib/supportedSymbols";

type SearchBarProps = {
  defaultValue?: string;
  compact?: boolean;
};

export default function SearchBar({
  defaultValue = "",
  compact = false
}: SearchBarProps) {
  const [symbol, setSymbol] = useState(defaultValue);
  const router = useRouter();
  const [message, setMessage] = useState<string | null>(null);
  const [messageTone, setMessageTone] = useState<"model" | "generic" | null>(null);

  useEffect(() => {
    setSymbol(defaultValue);
    setMessage(null);
    setMessageTone(null);
  }, [defaultValue]);

  // Route to the dashboard and annotate whether a dedicated model exists.
  const pushSymbol = (nextSymbol: string) => {
    const supported = Boolean(getSupportedSymbol(nextSymbol));
    setMessage(supported ? `${nextSymbol} uses its dedicated LSTM model.` : "No dedicated model — using generic prediction.");
    setMessageTone(supported ? "model" : "generic");
    router.push(`/stock/${encodeURIComponent(nextSymbol)}`);
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const clean = symbol.trim().toUpperCase();
    if (!clean) return;
    pushSymbol(clean);
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
      <div className="supported-section" style={{ marginTop: 10 }}>
        <p className="status-muted supported-note">Dedicated LSTM coverage</p>
        <div className="supported-chip-grid">
          {SUPPORTED_SYMBOLS.map((item) => (
            <button
              key={item.symbol}
              type="button"
              className="supported-chip"
              onClick={() => {
                setSymbol(item.symbol);
                pushSymbol(item.symbol);
              }}
            >
              <span className="supported-chip-symbol">{item.symbol}</span>
              <span className="supported-chip-name">{item.name}</span>
            </button>
          ))}
        </div>
        <p className="status-muted supported-note">
          You can still search any NSE/BSE symbol — unsupported tickers use the generic ensemble model.
        </p>
      </div>
      {message && (
        <p
          className={`status-muted ${messageTone === "generic" ? "status-generic" : "status-supported"}`}
          style={{ marginTop: 6 }}
        >
          {message}
        </p>
      )}
    </form>
  );
}

