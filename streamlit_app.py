"""Streamlit UI for the StoqIntelli stock predictor."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")

import pandas as pd
import streamlit as st

from data.cache import HybridCache
from data.fetcher import MarketDataFetcher
from data.preprocessor import FeatureEngineer
from pipeline.aggregator import EnsembleAggregator
from pipeline.predictor import PricePredictor
from pipeline.trainer import ALL_TIMEFRAMES
from supported_symbols import SUPPORTED_STOCKS

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "saved_models"
CACHE_PATH = BASE_DIR / "data" / "cache.sqlite"

DEFAULT_SYMBOL = ""

SUPPORTED_SYMBOL_CARDS: list[dict[str, str]] = [
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd"},
    {"symbol": "VBL", "name": "Varun Beverages Ltd"},
    {"symbol": "RVNL", "name": "Rail Vikas Nigam Ltd"},
    {"symbol": "TATATECH", "name": "Tata Technologies Ltd"},
    {"symbol": "INFY", "name": "Infosys Ltd"},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd"},
    {"symbol": "DMART", "name": "Avenue Supermarts Ltd"},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd"},
]

TIMEFRAME_LABELS: dict[str, str] = {
    "15m": "15 minutes",
    "1d": "1 day",
    "7d": "7 days",
    "1month": "1 month",
    "1y": "1 year",
}

CUSTOM_CSS = """
<style>
:root {
  --stq-bg: #f4efe5;
  --stq-surface: #ffffff;
  --stq-hero-start: #fef4e2;
  --stq-hero-end: #fffaf0;
  --stq-border: #e2d6c4;
  --stq-primary: #1d2437;
  --stq-secondary: #2c3a52;
  --stq-muted: #5a544b;
  --stq-chip-bg: #ffffff;
  --stq-chip-text: #1d2437;
  --stq-shadow: rgba(31, 42, 68, 0.10);
}

/* force light backgrounds even when system/streamlit picks dark */
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"], section.main, .block-container {
  background: var(--stq-bg) !important;
  color: var(--stq-primary) !important;
  font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp span, .stApp label, .stApp li {
  color: var(--stq-primary) !important;
}

.stApp p, .stApp span, .stApp li { font-weight: 400; }
.stApp h1, .stApp h2 { font-weight: 700; letter-spacing: -0.01em; }

/* Hero panel mirroring the Next.js reference */
.hero-card {
  background: linear-gradient(135deg, var(--stq-hero-start), var(--stq-hero-end));
  padding: 2.2rem 2.6rem 1.6rem;
  border-radius: 24px;
  border: 1px solid var(--stq-border);
  box-shadow: 0 24px 45px var(--stq-shadow);
  margin-bottom: 1.6rem;
}

.hero-card h2 {
  font-size: 2.1rem;
  margin-bottom: 0.35rem;
  color: var(--stq-primary) !important;
}

.hero-card p, .hero-note {
  font-size: 0.98rem;
  color: var(--stq-muted) !important;
}

.hero-note { margin-top: 0.6rem; }

/* Search input styled white pill */
.stTextInput > div > div {
  background: #ffffff !important;
  border-radius: 12px !important;
  border: 1px solid var(--stq-border) !important;
  box-shadow: 0 6px 16px rgba(31, 42, 68, 0.06);
}

.stTextInput > div > div > input {
  background: transparent !important;
  color: var(--stq-primary) !important;
  font-size: 1rem;
  padding: 0.85rem 1rem;
  border: none !important;
}

.stTextInput input::placeholder { color: #9b8f7f !important; }

label[data-testid="stWidgetLabel"] p {
  color: var(--stq-secondary) !important;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: none;
}

/* Workflow info cards */
.info-card {
  background: var(--stq-surface);
  border-radius: 18px;
  padding: 1.4rem 1.5rem;
  border: 1px solid var(--stq-border);
  box-shadow: 0 14px 30px var(--stq-shadow);
  height: 100%;
}

.info-card h3 {
  margin: 0 0 0.4rem;
  color: var(--stq-primary) !important;
  font-size: 1.1rem;
}

.info-card p {
  margin: 0;
  color: var(--stq-muted) !important;
}

.section-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--stq-secondary) !important;
  margin: 1.6rem 0 0.6rem;
}

/* Stock chip buttons */
div[data-testid="stHorizontalBlock"] div[data-testid="baseButton-secondary"] button {
  border-radius: 14px !important;
  border: 1px solid var(--stq-border) !important;
  background: var(--stq-chip-bg) !important;
  color: var(--stq-chip-text) !important;
  font-weight: 500 !important;
  min-height: 64px;
  white-space: pre-line;
  width: 100%;
  box-shadow: 0 6px 14px rgba(31, 42, 68, 0.05);
  text-align: left;
  padding: 0.7rem 1rem;
  line-height: 1.25;
}

div[data-testid="stHorizontalBlock"] div[data-testid="baseButton-secondary"] button p {
  color: var(--stq-chip-text) !important;
  font-weight: 500 !important;
}

div[data-testid="stHorizontalBlock"] div[data-testid="baseButton-secondary"] button:hover {
  border-color: #c9b89e !important;
  background: #fff7ea !important;
}

/* Primary Analyze CTA */
div[data-testid="baseButton-primary"] button {
  background: var(--stq-secondary) !important;
  color: #ffffff !important;
  font-weight: 600 !important;
  height: 52px;
  border-radius: 12px !important;
  border: none !important;
  box-shadow: 0 12px 24px rgba(44, 58, 82, 0.25);
}

div[data-testid="baseButton-primary"] button:hover {
  background: #1f2a44 !important;
}

div[data-testid="baseButton-primary"] button p {
  color: #ffffff !important;
}

/* Notifications + multiselect */
div[data-testid="stNotification"] {
  border-radius: 14px;
  background: #ffffff !important;
  border: 1px solid var(--stq-border) !important;
}

div[data-testid="stNotification"] p {
  color: var(--stq-primary) !important;
  font-weight: 500;
}

div[data-baseweb="select"] > div {
  background: #ffffff !important;
  border: 1px solid var(--stq-border) !important;
  border-radius: 12px !important;
  color: var(--stq-primary) !important;
}

div[data-baseweb="tag"], div[data-baseweb="tag"] * {
  background: var(--stq-secondary) !important;
  color: #ffffff !important;
  fill: #ffffff !important;
}

div[data-baseweb="tag"] svg { color: #ffffff !important; }

/* Footer line */
hr { border-color: var(--stq-border) !important; }
</style>
"""


def ensure_session_state() -> None:
    if "symbol_query" not in st.session_state:
        st.session_state.symbol_query = DEFAULT_SYMBOL
    if "selected_symbol" not in st.session_state:
        st.session_state.selected_symbol = None
    if "selected_timeframes" not in st.session_state:
        st.session_state.selected_timeframes = ALL_TIMEFRAMES.copy()
    if "should_fetch" not in st.session_state:
        st.session_state.should_fetch = False
    if "last_result" not in st.session_state:
        st.session_state.last_result = None


def set_symbol(symbol: str) -> None:
    normalized = symbol.strip().upper()
    if not normalized:
        return
    st.session_state.symbol_query = normalized
    st.session_state.selected_symbol = normalized
    st.session_state.should_fetch = True
    st.session_state.last_result = None


def on_timeframe_change() -> None:
    if st.session_state.get("selected_symbol"):
        st.session_state.should_fetch = True


def analyze_query() -> None:
    query = st.session_state.symbol_query.strip()
    if not query:
        st.session_state.should_fetch = False
        return
    set_symbol(query)


@st.cache_resource
def bootstrap_predictor() -> PricePredictor:
    cache = HybridCache(db_path=str(CACHE_PATH), default_ttl_seconds=60)
    fetcher = MarketDataFetcher(cache=cache)
    feature_engineer = FeatureEngineer()
    aggregator = EnsembleAggregator()
    return PricePredictor(
        saved_models_dir=MODEL_DIR,
        fetcher=fetcher,
        feature_engineer=feature_engineer,
        aggregator=aggregator,
    )


def format_predictions_table(payload: dict[str, Any]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for timeframe, details in payload.items():
        rows.append(
            {
                "Timeframe": TIMEFRAME_LABELS.get(timeframe, timeframe),
                "Predicted Price": details["predicted_price"],
                "Direction": details["direction"].title(),
                "Δ %": details["price_change_pct"],
                "Confidence %": details["confidence"],
                "Source": details["price_source"].upper(),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def info_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="info-card">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="StoqIntelli", page_icon="📈", layout="wide")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    ensure_session_state()

    predictor = bootstrap_predictor()

    st.markdown('<div class="hero-card">', unsafe_allow_html=True)
    st.markdown("## StoqIntelli")
    st.markdown("Search any stock symbol to view live market trend, timeframe forecasts, and confidence levels.")

    search_col, button_col = st.columns([5, 1])
    with search_col:
        st.text_input(
            "Search NSE symbol",
            placeholder="Search NSE symbol (e.g., RELIANCE, TCS, INFY)",
            key="symbol_query",
        )

    with button_col:
        st.button(
            "Analyze",
            type="primary",
            use_container_width=True,
            on_click=analyze_query,
        )

    st.markdown("### Dedicated LSTM coverage")
    chip_cols = st.columns(4)
    for idx, meta in enumerate(SUPPORTED_SYMBOL_CARDS):
        with chip_cols[idx % 4]:
            st.button(
                f"**{meta['symbol']}**  \n{meta['name']}",
                key=f"chip-{meta['symbol']}",
                on_click=set_symbol,
                args=(meta["symbol"],),
            )

    st.markdown(
        "<p class='hero-note'>You can still search any NSE/BSE symbol — unsupported tickers use the generic ensemble model.</p>",
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">Workflow snapshot</div>', unsafe_allow_html=True)
    info_columns = st.columns(3)
    with info_columns[0]:
        info_card("Timeframes", "15m, 1d, 7d, 1month, 1y")
    with info_columns[1]:
        info_card("Smart Compute", "Choose only the horizons you need to cut unnecessary computation.")
    with info_columns[2]:
        info_card("Output", "Price target, direction, and confidence for each horizon.")

    selected_timeframes = st.multiselect(
        "Select the horizons you want to evaluate",
        options=list(TIMEFRAME_LABELS.keys()),
        default=st.session_state.selected_timeframes,
        format_func=lambda key: TIMEFRAME_LABELS[key],
        key="selected_timeframes",
        on_change=on_timeframe_change,
    )

    if not selected_timeframes:
        st.warning("Select at least one timeframe to run predictions.")
        st.session_state.should_fetch = False

    status_symbol = st.session_state.selected_symbol
    supported = bool(status_symbol and status_symbol in SUPPORTED_STOCKS)
    if not status_symbol:
        st.info("Select a stock or use the search bar to start forecasting.")
    elif supported:
        st.success(f"{status_symbol} uses its dedicated LSTM model.")
    else:
        st.warning("No dedicated model — using generic prediction.")

    if st.session_state.should_fetch and selected_timeframes and status_symbol:
        with st.spinner("Crunching live market data..."):
            try:
                result = predictor.predict_symbol(status_symbol, timeframes=selected_timeframes)
                st.session_state.last_result = result
                st.session_state.should_fetch = False
            except Exception as exc:  # noqa: BLE001
                st.error(f"Unable to generate predictions for {status_symbol}: {exc}")
                st.session_state.should_fetch = False

    result_payload = st.session_state.get("last_result")
    if result_payload:
        current_price = result_payload.get("current_price")
        st.markdown(f"### Live market snapshot · ₹{current_price}")

        prediction_table = format_predictions_table(result_payload.get("predictions", {}))
        if not prediction_table.empty:
            st.dataframe(
                prediction_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Predicted Price": st.column_config.NumberColumn(format="₹%.2f"),
                    "Δ %": st.column_config.NumberColumn(format="%.2f%%"),
                    "Confidence %": st.column_config.NumberColumn(format="%.2f"),
                },
            )

        skipped = result_payload.get("skipped_timeframes", [])
        if skipped:
            skipped_text = "\n".join(f"• {row['timeframe']}: {row['reason']}" for row in skipped)
            st.warning(f"Some intervals were skipped:\n{skipped_text}")

    st.markdown("---")
    footer_cols = st.columns(2)
    footer_cols[0].markdown("Created by Ritesh Kushwaha")
    footer_cols[1].markdown("Project: [StoqIntelli on GitHub](https://github.com/Riteshkushwaha7/StoqIntelli)")


if __name__ == "__main__":
    main()
