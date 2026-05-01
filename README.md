# StoqIntelli

StoqIntelli is a full-stack stock prediction app:
- `ml-service`: FastAPI + LSTM prediction service
- `frontend`: Next.js 14 dashboard

Supported forecast timeframes: `15m`, `1d`, `7d`, `1month`, `1y`

Key behavior:
- Backend computes **only the requested timeframes** (`GET /predict/{symbol}?timeframes=...`).
- Each timeframe runs its own fetch + model (or adaptive fallback) so outputs differ.
- No mock or hardcoded price data.

---

## Local Run

### 1) Start backend
```bash
cd ml-service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Optional: train shared LSTM bundles so every timeframe has a non-naive model:
```bash
cd ml-service
python train_global.py  # uses RELIANCE data, saves __GLOBAL___{timeframe}.pt
```

### 2) Start frontend
```bash
cd frontend
npm install
npm run dev
```

Optional frontend env:
```bash
NEXT_PUBLIC_ML_SERVICE_URL=http://127.0.0.1:8000
```

---

## API

- `GET /health`
- `GET /stock/{symbol}`
- `GET /predict/{symbol}?timeframes=15m,1month`
- `POST /train/{symbol}?timeframes=15m,1d`

---

## Production Deployment

### A) Push code to GitHub
```bash
git init
git add .
git commit -m "stoqintelli prod"
git branch -M main
git remote add origin https://github.com/<you>/StoqIntelli.git
git push -u origin main
```

### B) Backend (Render or Railway)
- Render reads `render.yaml` and provisions a **Python** service.
- Railway: create a Python service pointing to `ml-service`, set start command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- Required env vars:
  - `ALLOWED_ORIGINS=https://<frontend-domain>`
  - Optional: `WEB_CONCURRENCY=2` (or higher for more workers)
- Health check: `/health`

### C) Frontend (Vercel or Railway)
- Root directory: `frontend`
- Env vars:
  - `NEXT_PUBLIC_ML_SERVICE_URL=https://<backend-domain>`

### D) Final sync
1. Deploy backend first and grab URL.
2. Deploy frontend with backend URL.
3. Update backend `ALLOWED_ORIGINS` with final frontend domain and redeploy backend once.

---

## Notes

- UI only sends selected timeframes, so backend load scales with user demand.
- For production backend scaling, raise `WEB_CONCURRENCY` and/or allocate more RAM.
- Train per-symbol LSTM models via `POST /train/{symbol}` when you have historical data. If a symbol-specific weight is missing, the predictor now checks for shared `__GLOBAL___{timeframe}.pt` weights before falling back to adaptive heuristics.
