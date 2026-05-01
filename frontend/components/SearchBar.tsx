"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { SUPPORTED_SYMBOLS, isSupportedSymbol } from "@/lib/supportedSymbols";

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
  const allowedSymbols = useMemo(() => SUPPORTED_SYMBOLS.map((item) => item.symbol), []);

  useEffect(() => {
    setSymbol(defaultValue);
  }, [defaultValue]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const clean = symbol.trim().toUpperCase();
    if (!clean) return;
    if (!isSupportedSymbol(clean)) {
      setMessage(`Coming soon: ${clean}. Currently live for ${allowedSymbols.join(", ")}.`);
      return;
    }
    setMessage(null);
    router.push(`/stock/${encodeURIComponent(clean)}`);
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
      {message && <p className="status-muted" style={{ marginTop: 6 }}>{message}</p>}
      {!message && (
        <p className="status-muted" style={{ marginTop: 6 }}>
          Supported: {SUPPORTED_SYMBOLS.map((item) => item.symbol).join(", ")}
        </p>
      )}
    </form>
  );
}

