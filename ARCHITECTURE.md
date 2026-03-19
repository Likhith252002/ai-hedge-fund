# Architecture

A deep-dive into how the AI Hedge Fund multi-agent system is designed, why each decision was made, and how the pieces fit together.

---

## System overview

```
Browser
  │  HTTP :80  /api/*
  │  WS   :80  /ws/*
  ▼
nginx  (reverse proxy)
  │  proxy_pass → localhost:8000
  ▼
FastAPI  (uvicorn · systemd)
  │
  ├── GET  /api/v1/stock/{ticker}   ──→ StockDataTool → yfinance / Yahoo v8 API
  ├── GET  /api/v1/news/{ticker}    ──→ NewsFetcher   → 4 cascading sources
  ├── GET  /api/v1/history          ──→ SQLite
  ├── GET  /metrics                 ──→ SQLite aggregate
  └── WS   /ws/analyse
          │
          ▼
     LangGraph pipeline
          │
          ├── research_quant node (parallel asyncio.gather)
          │      ├── ResearchAgent  →  fundamentals + news + research_summary
          │      └── QuantAgent     →  RSI, MACD, SMA, Bollinger → quant_signal
          │
          ├── bull node
          │      └── BullAgent (Claude API) → bull_thesis
          │
          ├── bear node
          │      └── BearAgent (Claude API) → bear_thesis
          │
          └── decide node
                 └── DecisionAgent (Claude API) → BUY/SELL/HOLD + confidence + position_size
```

---

## Agent responsibilities

### ResearchAgent

**Input:** ticker symbol
**Output:** `fundamentals`, `news`, `research_summary`

- Calls `StockDataTool.get_fundamentals()` — yfinance `.info` dict (P/E, ROE, revenue growth, analyst target, etc.)
- Calls `NewsFetcher.get_news()` — up to 10 recent headlines from 4 cascading sources
- Computes average news sentiment score
- Produces a one-line `research_summary` string consumed by downstream LLM agents

### QuantAgent

**Input:** ticker symbol
**Output:** `indicators`, `quant_signal`

- Calls `StockDataTool.get_technical_indicators()` — 1-year OHLCV → RSI-14, MACD, SMA 20/50/200, Bollinger Bands, 52-week range
- Signal scoring: each of RSI, MACD, and SMA crossover casts a vote (BUY / SELL / neutral); majority wins
- Falls back to pure-pandas RSI and MACD calculation if the `ta` library fails

### BullAgent

**Input:** `research_summary`, `quant_signal`, `indicators`, `fundamentals`, `news`
**Output:** `bull_thesis` (prose, ~4 paragraphs)

- Calls `anthropic.AsyncAnthropic` directly (bypasses LangChain for reliability)
- Prompt instructs the model to act as a bullish equity analyst; forces plain prose with no markdown
- Constrained to 600 max tokens for concision

### BearAgent

**Input:** same as BullAgent
**Output:** `bear_thesis` (~4 paragraphs)

- Mirror image of BullAgent: skeptical analyst building the strongest possible bear case
- Same direct Anthropic client approach

### DecisionAgent

**Input:** `bull_thesis`, `bear_thesis`, `quant_signal`, `indicators`, `fundamentals`
**Output:** `decision` → `{ action, confidence, position_size, rationale }`

- Presents both theses + all quant data to Claude in a structured prompt
- Prompt explicitly forces a definitive recommendation — no hedging allowed
- Strict output format parsed with `_parse_decision()`: `DECISION:`, `CONFIDENCE:`, `POSITION_SIZE:`, `RATIONALE:`
- Confidence clamped to [30, 90]; position size clamped to [0, 10%]

---

## Why this architecture

### Parallel Research + Quant

The Research and Quant agents are independent: Research fetches fundamentals and news from external APIs; Quant fetches price history and runs pure math. They share no data and neither depends on the other's output. Running them with `asyncio.gather` cuts total analysis time roughly in half versus sequential execution.

### Sequential Bull → Bear → Decide

The LLM agents are sequential by necessity: Bull and Bear both need the research summary and quant signal (produced by the parallel node), and the Decision agent needs both theses. This dependency chain is encoded directly in the LangGraph edge list.

The Bull and Bear agents run back-to-back rather than in parallel even though they don't depend on each other. This was a deliberate choice: running two concurrent Claude API calls would double the API load with no latency benefit from the user's perspective (the Decision agent still has to wait for both).

### Streaming over WebSocket

Instead of a single long HTTP request, the frontend connects via WebSocket and receives one JSON message per agent completion. This lets the UI display each agent's output the moment it's ready — the user sees Research & Quant results after ~5 s, the Bull thesis after ~15 s, etc., rather than staring at a spinner for 30 s.

### Direct Anthropic client (no LangChain for LLM calls)

The Bull, Bear, and Decision agents call `anthropic.AsyncAnthropic` directly. Earlier versions used `langchain-anthropic.ChatAnthropic` but it silently failed with `claude-sonnet-4-6` model IDs in the pinned version (0.1.15), always returning a default HOLD with 40% confidence. The direct client is simpler, more reliable, and has no abstraction overhead.

LangChain / LangGraph are still used for the StateGraph pipeline orchestration — just not for the LLM calls themselves.

---

## Data flow — WebSocket message sequence

```
Client                          Server
  │                               │
  │── connect /ws/analyse ────────▶│
  │◀── (accept) ──────────────────│
  │── {"ticker": "NVDA"} ─────────▶│
  │                               │  [research + quant running in parallel]
  │◀── agent_complete research_quant │  ~5-8 s
  │                               │  [bull agent running]
  │◀── agent_complete bull ────────│  ~10-15 s
  │                               │  [bear agent running]
  │◀── agent_complete bear ────────│  ~15-22 s
  │                               │  [decision agent running]
  │◀── agent_complete decide ──────│  ~25-35 s
  │◀── complete {full state} ──────│
  │── (close) ────────────────────▶│
```

---

## Data sources

### Stock prices and fundamentals — StockDataTool

| Source | Used for | Fallback order |
|:---|:---|:---:|
| `yfinance.Ticker.history()` | OHLCV (price chart, technicals) | 1st |
| Yahoo Finance v8 chart API | OHLCV fallback on cloud IPs | 2nd |
| `yfinance.Ticker.info` | Fundamentals (P/E, ROE, etc.) | 1st |
| `_FALLBACK_FUNDAMENTALS` dict | Market-average mock fundamentals | Last |

yfinance is frequently rate-limited from cloud provider IPs. Every call uses a `requests.Session` with a browser User-Agent and retries up to 3 times before falling back. The Yahoo Finance v8 REST API is used as a last resort for OHLCV data.

### News — NewsFetcher

Four sources are tried in order; the first to return ≥ 3 articles wins:

1. `yfinance.Ticker.news` — structured JSON, fastest
2. `query1.finance.yahoo.com/v1/finance/search` — public JSON endpoint, no auth
3. Alpha Vantage `NEWS_SENTIMENT` (demo key) — pre-scored sentiment
4. Yahoo Finance RSS feed parsed with BeautifulSoup — last resort

Sentiment is scored with a rule-based keyword matcher using ~60 positive and ~60 negative financial terms. Scores are in [-1, +1].

---

## Persistence — SQLite

All completed analyses are stored in `backend/data/analyses.db`:

```sql
CREATE TABLE analyses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker            TEXT    NOT NULL,
    created_at        TEXT    NOT NULL,
    action            TEXT,               -- BUY / SELL / HOLD
    confidence        INTEGER,            -- 30–90
    position_size     REAL,               -- 0–10 %
    quant_signal      TEXT,               -- BUY / SELL / NEUTRAL
    execution_time_ms INTEGER,
    result_json       TEXT    NOT NULL    -- full state as JSON
);
```

**24-hour cache:** Before running a new analysis, the backend checks for a cached result for the same ticker within the last 24 hours. Cache hits are served instantly from SQLite and the frontend shows a `_cached: true` flag.

**Analytics endpoint:** `GET /metrics` aggregates total analyses, average execution time, top stocks, and BUY/SELL/HOLD distribution — with zero additional infrastructure.

---

## Deployment

```
EC2 t2.micro (Ubuntu 22.04)
├── /home/ubuntu/ai-hedge-fund/
│   ├── backend/                   ← uvicorn runs from here
│   ├── frontend/                  ← build artifacts only
│   ├── venv/                      ← Python 3.11 virtualenv
│   └── .env                       ← ANTHROPIC_API_KEY (not in git)
├── /var/www/ai-hedge-fund/        ← React build (served by nginx)
├── /etc/nginx/sites-enabled/      ← nginx.conf symlinked here
└── /etc/systemd/system/           ← ai-hedge-fund.service
```

nginx sits in front of everything on port 80. Static files are served directly from disk (fast); `/api/*` and `/ws/*` are proxied to uvicorn on `localhost:8000` which is not exposed to the internet.

`deploy.sh` automates the full redeploy cycle: `git pull` → `pip install` → `npm run build` → copy static files → `systemctl restart` → `nginx -t && reload`.

---

## Scalability considerations

The current single-EC2 architecture is appropriate for a portfolio/demo project. For production scale:

- **Horizontal scaling:** The FastAPI app is stateless (session data lives only in the WebSocket connection). Multiple uvicorn workers behind nginx can handle concurrent analyses. SQLite would be replaced with PostgreSQL.
- **Async LLM calls:** Bull, Bear, and Decision agents use `anthropic.AsyncAnthropic` — they are already fully async and would not block under concurrent load.
- **Rate limiting:** The in-process rate limiter in `routes.py` is per-worker. A shared Redis store (e.g. with `slowapi`) would be needed for multi-worker deployments.
- **Cache warming:** The 24-hour SQLite cache significantly reduces API calls for popular tickers. A Redis cache would allow sharing across workers.
