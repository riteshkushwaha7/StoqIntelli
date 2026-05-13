# StoqIntelli

StoqIntelli is now a single Streamlit experience that bundles the resilient LSTM pipeline, predictor, and UI in one Python service. Users can search NSE symbols, tap dedicated chips for the eight supported stocks, and request custom timeframe forecasts (15m, 1d, 7d, 1month, 1y). Every prediction run fetches fresh Yahoo Finance data, loads the appropriate trained bundle (or shared fallback), and surfaces confidence/direction metadata.

---

## Repo layout

```
data/                # Fetch/cache helpers + feature engineering inputs
models/              # LSTM architectures for short/mid/long horizons
pipeline/            # Trainer + predictor orchestration
saved_models/        # .pt bundles (per symbol + shared __GLOBAL__ weights)
streamlit_app.py     # Public UI + orchestrator
train_global.py      # Batch training entry point for all supported symbols
requirements.txt     # Python dependencies (FastAPI still available for CLI/API reuse)
```

---

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
streamlit run streamlit_app.py --server.port 8501
```

The UI runs entirely locally and shares the same artifacts as production (reads/writes `saved_models/`).

### Training bundles

```bash
python train_global.py
# or train a single symbol/timeframe via pipeline.trainer.LSTMTrainer
```

Each trained timeframe saves `SYMBOL_{timeframe}.pt` under `saved_models/`. Missing dedicated weights automatically fall back to the shared `__GLOBAL___{timeframe}.pt` bundles.

---

## Deployment (Render example)

1. Push the repo to GitHub.
2. Render automatically detects `render.yaml` and provisions a Python service rooted at the repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`
5. Health check path: `/`

Set any optional environment variables (e.g., cache TTL overrides) directly in the Render dashboard.

---

## Notes

- The FastAPI app (`main.py`) and trainer modules remain available for scripting or future API surfaces, but Streamlit is the primary user interface.
- `saved_models/` should not be committed except for placeholder `.gitkeep`; model artifacts are regenerated during training.
- Keep your deployment on Python 3.10 (see `runtime.txt`) to guarantee pre-built `pydantic-core` wheels.
