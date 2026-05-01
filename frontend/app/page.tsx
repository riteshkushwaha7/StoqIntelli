import SearchBar from "@/components/SearchBar";

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero">
        <h1 className="title">StoqIntelli</h1>
        <p className="subtitle">
          Search any stock symbol to view live market trend, timeframe forecasts, and confidence levels.
        </p>
        <SearchBar />
      </section>
      <section className="grid" style={{ marginTop: 18 }}>
        <article className="card" style={{ gridColumn: "span 4" }}>
          <h3 style={{ marginTop: 0 }}>Timeframes</h3>
          <p className="subtitle" style={{ marginBottom: 0 }}>
            15m, 1d, 7d, 1month, 1y
          </p>
        </article>
        <article className="card" style={{ gridColumn: "span 4" }}>
          <h3 style={{ marginTop: 0 }}>Smart Compute</h3>
          <p className="subtitle" style={{ marginBottom: 0 }}>
            Choose only the horizons you need. We compute only selected timeframes.
          </p>
        </article>
        <article className="card" style={{ gridColumn: "span 4" }}>
          <h3 style={{ marginTop: 0 }}>Output</h3>
          <p className="subtitle" style={{ marginBottom: 0 }}>
            Price target, direction (up/down/flat), and confidence percentage for each selected horizon.
          </p>
        </article>
      </section>
    </main>
  );
}
