# AI Hedge Fund — Session Context

> Last updated: 2026-03-12
> GitHub: https://github.com/Likhith252002/ai-hedge-fund
> Local path: ~/Desktop/ai-hedge-fund

---

## 1. Current Project State

### What is built and working

#### Backend (FastAPI · Python 3.11)
- **FastAPI app** running on port 8000 with CORS middleware
- **REST endpoints** (all tested and returning real data):
  - `GET  /health` and `GET /api/health` → `{"status":"ok","service":"ai-hedge-fund"}`
  - `POST /api/v1/analyse` → runs full 5-agent LangGraph pipeline, returns complete state
  - `GET  /api/v1/stock/{ticker}` → fundamentals + 3mo OHLCV chart data
  - `GET  /api/v1/news/{ticker}` → 10 recent news articles

#### LangGraph Pipeline (`backend/graph/hedge_fund_graph.py`)
Sequential pipeline (fan-out not supported in LangGraph 0.1.14 without annotated state):
```
ResearchAgent → QuantAgent → BullAgent → BearAgent → DecisionAgent(decide)
```
- Uses `HedgeFundState` TypedDict with keys:
  `ticker, fundamentals, news, research_summary, indicators, quant_signal, bull_thesis, bear_thesis, decision, error`
- Node named `"decide"` (not `"decision"`) to avoid LangGraph state key conflict

#### Agents (`backend/agents/`)
- **ResearchAgent** — calls `get_fundamentals()` + `get_news()`, builds `research_summary` string
- **QuantAgent** — calls `get_price_history()` + `compute_indicators()`, outputs `quant_signal`: BUY/SELL/NEUTRAL
- **BullAgent** — Claude LLM or rule-based fallback, writes `bull_thesis`
- **BearAgent** — Claude LLM or rule-based fallback, writes `bear_thesis`
- **DecisionAgent** — synthesises all → `decision: {action, confidence, position_size, rationale}`
- LLM is optional: if no `ANTHROPIC_API_KEY`, all agents use rule-based fallback

#### Tools (`backend/tools/`)
**StockDataTool** (`stock_data.py`) — fully implemented and tested:
- `get_price_history(ticker, period)` → OHLCV DataFrame, fixes yfinance 1.x MultiIndex columns
- `get_current_price(ticker)` → `{ticker, price, change_pct, volume, market_cap}`
- `get_technical_indicators(ticker)` → RSI-14, MACD+signal+hist, SMA 20/50/200, Bollinger Bands, avg_volume_10d, price_vs_52w_high/low (uses `ta` library)
- `get_fundamentals(ticker)` → 12 metrics: pe_ratio, forward_pe, peg_ratio, price_to_book, debt_to_equity, roe, revenue_growth, earnings_growth, profit_margin, current_ratio, analyst_target, recommendation_mean
- Module-level helpers for backward compat: `get_fundamentals()`, `get_price_history()`, `get_ohlcv_list()`

**NewsFetcher** (`news_fetcher.py`) — fully implemented and tested:
- `get_news(ticker, company_name)` → up to 10 articles from yfinance + Alpha Vantage (demo key, graceful fallback). Each: `{title, summary, source, published_at, sentiment_score, url}`
- `get_reddit_sentiment(ticker)` → Reddit search API → `{mention_count, avg_sentiment, top_posts}`
- `analyze_sentiment(text)` → rule-based score [-1.0, 1.0] using financial keyword lists

#### Frontend (React 18 · Vite · TailwindCSS · Chart.js)
- **App.jsx** — main layout, calls `/api/v1/stock` + `/api/v1/analyse` in parallel on submit
- **TickerInput.jsx** — text input + quick-pick buttons (AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN)
- **StockChart.jsx** — Chart.js line chart, green/red based on trend, 3mo OHLCV
- **AgentStream.jsx** — shows output from all 4 agents (Research, Quant, Bull, Bear) with loading skeletons
- **DecisionCard.jsx** — BUY/SELL/HOLD badge, confidence bar, position size, rationale, "Add to Portfolio" button
- **PortfolioTracker.jsx** — in-memory portfolio list with action/confidence/position per ticker
- `VITE_API_URL` env var used for production API base URL (defaults to `""` which uses Vite proxy)

---

## 2. Exact File Structure

```
ai-hedge-fund/
├── backend/
│   ├── agents/
│   │   ├── __init__.py                  ← exports all 5 agents
│   │   ├── research_agent.py            ← fetches fundamentals + news
│   │   ├── quant_agent.py               ← RSI/MACD → BUY/SELL/NEUTRAL
│   │   ├── bull_agent.py                ← LLM or rule-based bull thesis
│   │   ├── bear_agent.py                ← LLM or rule-based bear thesis
│   │   └── decision_agent.py            ← synthesises → action + confidence
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── stock_data.py                ← StockDataTool class (fully built)
│   │   └── news_fetcher.py              ← NewsFetcher class (fully built)
│   ├── graph/
│   │   ├── __init__.py
│   │   └── hedge_fund_graph.py          ← LangGraph StateGraph pipeline
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                      ← FastAPI app + CORS
│   │   └── routes.py                    ← /health, /analyse, /stock, /news
│   ├── requirements.txt                 ← all deps including yfinance>=1.0.0
│   ├── Procfile                         ← web: uvicorn api.main:app ...
│   └── nixpacks.toml                    ← python311 + pip, Railway deploy
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TickerInput.jsx          ← ticker input + quick-pick buttons
│   │   │   ├── AgentStream.jsx          ← shows all agent outputs
│   │   │   ├── StockChart.jsx           ← Chart.js price chart
│   │   │   ├── DecisionCard.jsx         ← BUY/SELL/HOLD + add to portfolio
│   │   │   └── PortfolioTracker.jsx     ← in-memory portfolio list
│   │   ├── App.jsx                      ← main layout + API calls
│   │   ├── main.jsx                     ← React root mount
│   │   └── index.css                    ← Tailwind base
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js                   ← proxy /api → localhost:8000
│   ├── tailwind.config.js
│   └── postcss.config.js
├── .env.example                         ← ANTHROPIC_API_KEY, VITE_API_URL
├── .gitignore
├── docker-compose.yml
├── README.md
└── CONTEXT.md                           ← this file
```

---

## 3. What Needs to Be Built Next

### Prompt 3 — Wire agents to use StockDataTool + NewsFetcher properly
The agents currently use old module-level helpers. Update them to use the new classes:
- `ResearchAgent` → use `StockDataTool().get_fundamentals()` + `NewsFetcher().get_news()`
- `QuantAgent` → use `StockDataTool().get_technical_indicators()` (replaces manual MACD/RSI code)
- `BullAgent` / `BearAgent` → pass `indicators` dict + `fundamentals` dict into LLM prompt
- `DecisionAgent` → include `current_price` and `indicators` in LLM prompt context

### Prompt 4 — Improve LLM prompts + streaming
- Add proper structured output parsing for LLM responses (use Pydantic models)
- Add a `POST /api/v1/analyse/stream` endpoint that streams agent progress via SSE
  so the frontend can show each agent completing in real time
- Frontend `AgentStream.jsx` should subscribe to the SSE stream and show agents
  completing one-by-one with a checkmark

### Prompt 5 — Portfolio & position sizing
- Add `backend/portfolio/` module:
  - `portfolio_manager.py` — tracks positions, calculates P&L, enforces max position limits
  - `risk_manager.py` — checks Kelly criterion, max drawdown, concentration risk
- Add endpoints:
  - `GET  /api/v1/portfolio` — current positions
  - `POST /api/v1/portfolio/add` — add position
  - `DELETE /api/v1/portfolio/{ticker}` — remove position
- Frontend `PortfolioTracker.jsx` → fetch from API, show real P&L

### Prompt 6 — Historical backtesting
- Add `backend/backtest/` module:
  - `backtester.py` — runs the full agent pipeline on historical data windows
  - Returns win rate, Sharpe ratio, max drawdown, total return
- Add `POST /api/v1/backtest` endpoint (ticker + date range)
- Frontend: new `BacktestPanel.jsx` component showing backtest results chart

### Prompt 7 — Deploy to Railway
- Backend service: root dir = `backend`, auto-detects `nixpacks.toml`
- Frontend service: root dir = `frontend`, build = `npm run build`, serve = `npx serve dist`
- Railway env vars needed:
  - Backend: `ANTHROPIC_API_KEY`, `ALLOWED_ORIGINS`
  - Frontend: `VITE_API_URL=https://<backend>.up.railway.app`

---

## 4. Key Decisions Made

| Decision | Choice | Reason |
|---|---|---|
| Agent orchestration | LangGraph 0.1.14 sequential (not fan-out) | Fan-out raises `ValueError: Already found path` without annotated state |
| Node naming | `"decide"` not `"decision"` | LangGraph forbids node names that match state keys |
| yfinance version | `>=1.0.0` | v0.2.40 got 429 rate limits; v1.x fixed it |
| yfinance columns | Flatten MultiIndex `('Close','AAPL')` → `'close'` | yfinance 1.x changed column structure |
| yfinance news | Parse `item['content']['title']` not `item['title']` | yfinance 1.x changed news schema |
| LLM | Claude `claude-sonnet-4-6` via `langchain-anthropic` | Optional — graceful rule-based fallback if no API key |
| Sentiment | Rule-based keyword matching | No external API needed, works offline |
| Frontend API calls | `VITE_API_URL` env var + `""` fallback | Vite proxy handles localhost; Railway needs explicit URL |
| Railway build | `python311Packages.pip` in nixpacks | `python311` alone doesn't put `pip` on PATH |
| Port | Backend 8000, Frontend 5173 | Standard FastAPI/Vite defaults |

---

## 5. How to Resume

```bash
# Start backend
cd ~/Desktop/ai-hedge-fund/backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start frontend (new terminal)
cd ~/Desktop/ai-hedge-fund/frontend
npm install   # first time only
npm run dev

# Test backend
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/analyse \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL","use_llm":false}'
```

Set `ANTHROPIC_API_KEY` in `.env` to enable Claude LLM agents.
