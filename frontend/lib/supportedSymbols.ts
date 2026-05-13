export type SupportedSymbol = {
  symbol: string;
  name: string;
  ticker: string;
  note?: string;
};

// Dedicated model coverage mirrors ml-service/supported_symbols.py
export const SUPPORTED_SYMBOLS: SupportedSymbol[] = [
  { symbol: "RELIANCE", name: "Reliance Industries Ltd", ticker: "RELIANCE.NS", note: "Core benchmark" },
  { symbol: "VBL", name: "Varun Beverages Ltd", ticker: "VBL.NS", note: "Beverages" },
  { symbol: "RVNL", name: "Rail Vikas Nigam Ltd", ticker: "RVNL.NS", note: "Infra momentum" },
  { symbol: "TATATECH", name: "Tata Technologies Ltd", ticker: "TATATECH.NS", note: "EV + auto design" },
  { symbol: "INFY", name: "Infosys Ltd", ticker: "INFY.NS", note: "Tier-1 IT" },
  { symbol: "KPITTECH", name: "KPIT Technologies Ltd", ticker: "KPITTECH.NS", note: "Auto software" },
  { symbol: "DMART", name: "Avenue Supermarts Ltd", ticker: "DMART.NS", note: "Retail" },
  { symbol: "TATAELXSI", name: "Tata Elxsi Ltd", ticker: "TATAELXSI.NS", note: "Design + ER&D" }
];

const SYMBOL_SET = new Set(SUPPORTED_SYMBOLS.map((item) => item.symbol));
const SYMBOL_MAP = new Map(SUPPORTED_SYMBOLS.map((item) => [item.symbol, item]));

export function isSupportedSymbol(symbol: string): boolean {
  return SYMBOL_SET.has(symbol.trim().toUpperCase());
}

export function getSupportedSymbol(symbol: string): SupportedSymbol | undefined {
  return SYMBOL_MAP.get(symbol.trim().toUpperCase());
}
