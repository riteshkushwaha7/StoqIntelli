export type SupportedSymbol = {
  symbol: string;
  name: string;
  weight: string;
};

export const SUPPORTED_SYMBOLS: SupportedSymbol[] = [
  { symbol: "RELIANCE", name: "Reliance Industries Ltd", weight: "~12.5% of Nifty 50" },
  { symbol: "HDFCBANK", name: "HDFC Bank Ltd", weight: "~7.6%" },
  { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", weight: "~7.4%" },
  { symbol: "SBIN", name: "State Bank of India", weight: "~6.3%" },
  { symbol: "ICICIBANK", name: "ICICI Bank Ltd", weight: "~6%" }
];

const SYMBOL_SET = new Set(SUPPORTED_SYMBOLS.map((item) => item.symbol));

export function isSupportedSymbol(symbol: string): boolean {
  return SYMBOL_SET.has(symbol.trim().toUpperCase());
}
