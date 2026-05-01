# TODO: Remove Sentiment Analysis & Fix Timeframe/Analyze Issues

## Backend — Remove Sentiment
- [x] Delete `ml-service/models/sentiment.py`
- [x] Edit `ml-service/data/fetcher.py` — remove `fetch_news_rss_url` and `quote_plus` import
- [x] Edit `ml-service/models/__init__.py` — remove sentiment from docstring
- [x] Edit `ml-service/pipeline/aggregator.py` — strip sentiment blending, compute direction/confidence/change_pct from price only, remove `sentiment_adjustment`
- [x] Edit `ml-service/pipeline/predictor.py` — remove `SentimentAnalyzer` import/usage, drop sentiment from response
- [x] Edit `ml-service/main.py` — remove `SentimentAnalyzer` import/instantiation, update `PricePredictor` args, update description
- [x] Edit `ml-service/requirements.txt` — remove `feedparser`, `transformers`, `accelerate`, `beautifulsoup4`

## Frontend — Remove Sentiment
- [x] Delete `frontend/components/SentimentGauge.tsx`
- [x] Edit `frontend/lib/api.ts` — remove `SentimentResponse`, `sentiment_adjustment`, and `sentiment` field
- [x] Edit `frontend/app/stock/[symbol]/page.tsx` — remove `SentimentGauge` import, remove sentiment card, remove gauge from grid
- [x] Edit `frontend/app/page.tsx` — remove "sentiment direction" from subtitle
- [x] Edit `frontend/app/layout.tsx` — remove "sentiment analysis" from description
- [x] Edit `README.md` — remove sentiment mentions

## Fix Timeframe Selection & Analyze Button
- [x] Edit `frontend/components/SearchBar.tsx` — fix `toggleAll` to toggle between all and none (`[]`)

## Verification
- [x] Frontend build check: `cd frontend; npm run build` — passed
- [x] Backend import check: `cd ml-service; python -c "import main"` — passed

