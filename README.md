# StoqIntelli

StoqIntelli is a full-stack stock prediction app:
- `ml-service`: FastAPI + LSTM + sentiment ensemble
- `frontend`: Next.js 14 dashboard

Supported forecast timeframes:
- `15m`, `1d`, `7d`, `1month`, `1y`

Computation optimization:
- Backend computes **only selected timeframes** from `timeframes` query param.
- If user selects 2 horizons, only those 2 are fetched/inferred.

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

## Production Deployment (Recommended)

## A) Push code to GitHub
1. Create repo: `StoqIntelli`
2. From project root:
```bash
git init
git add .
git commit -m "StoqIntelli production setup"
git branch -M main
git remote add origin https://github.com/<your-username>/StoqIntelli.git
git push -u origin main
```

## B) Deploy FastAPI backend on Render

This repo includes:
- `ml-service/Dockerfile`
- `render.yaml`

Steps:
1. Go to Render -> New -> Blueprint
2. Connect your GitHub repo
3. Render reads `render.yaml` and creates `stoqintelli-ml`
4. Set env var in Render:
   - `ALLOWED_ORIGINS=https://<your-frontend-domain>`
5. Deploy and copy backend URL (example: `https://stoqintelli-ml.onrender.com`)

Health check:
- `https://stoqintelli-ml.onrender.com/health`

## C) Deploy frontend on Vercel
1. Go to Vercel -> New Project -> import same repo
2. Set Root Directory to `frontend`
3. Add env var:
   - `NEXT_PUBLIC_ML_SERVICE_URL=https://stoqintelli-ml.onrender.com`
4. Deploy

## D) Final CORS sync
After Vercel gives final domain:
1. Update Render env var `ALLOWED_ORIGINS` to that exact Vercel domain
2. Redeploy backend

---

## Notes

- First sentiment request can be slower due to model warmup.
- Use selected timeframes in UI near `Analyze` button to avoid unnecessary compute.
- For production backend scaling, increase `WEB_CONCURRENCY` in Render env if needed.
