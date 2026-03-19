<div align="center">

```
 █████╗ ██╗    ██╗  ██╗███████╗██████╗  ██████╗ ███████╗    ███████╗██╗   ██╗███╗   ██╗██████╗
██╔══██╗██║    ██║  ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝    ██╔════╝██║   ██║████╗  ██║██╔══██╗
███████║██║    ███████║█████╗  ██║  ██║██║  ███╗█████╗      █████╗  ██║   ██║██╔██╗ ██║██║  ██║
██╔══██║██║    ██╔══██║██╔══╝  ██║  ██║██║   ██║██╔══╝      ██╔══╝  ██║   ██║██║╚██╗██║██║  ██║
██║  ██║██║    ██║  ██║███████╗██████╔╝╚██████╔╝███████╗    ██║     ╚██████╔╝██║ ╚████║██████╔╝
╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚═════╝
```

### Five AI analysts debate any stock in real time — and deliver a verdict

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.14-FF6B35?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![AWS EC2](https://img.shields.io/badge/Deployed_on-AWS_EC2-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white)](http://18.224.16.180)
[![Live Demo](https://img.shields.io/badge/Live_Demo-Online-brightgreen?style=for-the-badge&logo=statuspage&logoColor=white)](http://18.224.16.180)
[![Tests](https://img.shields.io/badge/Tests-27_passing-success?style=for-the-badge&logo=pytest&logoColor=white)](backend/tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

## 🚀 [http://18.224.16.180](http://18.224.16.180) — Live on AWS EC2

<br/>

**[📖 How It Works](#-how-it-works)** &nbsp;•&nbsp;
**[🏗️ Architecture](ARCHITECTURE.md)** &nbsp;•&nbsp;
**[📊 Examples](EXAMPLES.md)** &nbsp;•&nbsp;
**[🚀 Quick Start](#-quick-start)** &nbsp;•&nbsp;
**[🐛 Report Bug](https://github.com/Likhith252002/ai-hedge-fund/issues)**

<br/>

> Enter any ticker — five specialized AI agents debate it and return a concrete BUY, SELL, or HOLD with a confidence score, position sizing recommendation, and cited rationale. Not a ChatGPT wrapper: a LangGraph multi-agent pipeline running Research, Quant, Bull, Bear, and Decision agents in a coordinated workflow with real market data.

</div>

---

## 🎯 Why This Stands Out

Most "AI stock analysis" tools are a single LLM call with a generic prompt. This is different:

| | This project | Typical AI stock app |
|:---|:---:|:---:|
| **Architecture** | 5 specialized agents in a LangGraph pipeline | Single LLM prompt |
| **Quantitative analysis** | RSI, MACD, Bollinger, SMA 20/50/200 | None |
| **Adversarial reasoning** | Dedicated Bull AND Bear agents debate each other | One-sided narrative |
| **Data integration** | Live yfinance data + 4 news sources | Static/hallucinated |
| **Streaming** | Real-time WebSocket — watch each agent complete live | Blocking HTTP |
| **Persistence** | SQLite history + 24h cache + `/metrics` endpoint | Stateless |
| **Production deployment** | AWS EC2 · nginx · systemd | localhost only |
| **Test coverage** | 27 pytest tests across API, validation, sentiment, DB | None |

---

## ⚡ Performance

<div align="center">

| Metric | Value |
|:---|:---:|
| ⏱️ End-to-end analysis | ~25–35 seconds |
| 🤖 Specialized agents | 5 (Research, Quant, Bull, Bear, Decision) |
| ⚡ Parallel execution | Research + Quant run concurrently |
| 📡 Streaming | Real-time WebSocket per-agent updates |
| 📊 Fundamental metrics | 12+ (P/E, ROE, revenue growth, margins...) |
| 📈 Technical indicators | RSI, MACD, Bollinger Bands, SMA 20/50/200 |
| 🗄️ Cache | 24-hour SQLite cache — repeat lookups are instant |
| 🧪 Test coverage | 27 passing tests |

</div>

---

## 🏗️ Architecture

```
Browser
  │  HTTP :80  /api/*       WS :80  /ws/*
  ▼
nginx  (reverse proxy · port 80)
  │  proxy → localhost:8000
  ▼
FastAPI + Uvicorn  (systemd · AWS EC2 t2.micro)
  │
  └── WS /ws/analyse
          │
          ▼
     LangGraph StateGraph
          │
          ├── research_quant  ←─── asyncio.gather (parallel)
          │      ├── ResearchAgent  →  yfinance fundamentals + news sentiment
          │      └── QuantAgent     →  RSI·MACD·SMA·Bollinger → quant_signal
          │
          ├── bull    BullAgent (Claude Sonnet 4.6)  →  bullish thesis
          ├── bear    BearAgent (Claude Sonnet 4.6)  →  bearish thesis
          └── decide  DecisionAgent (Claude Sonnet 4.6)  →  BUY/SELL/HOLD
                                                            confidence %
                                                            position size %
```

**Full technical deep-dive:** [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 🤖 How It Works

**1. Enter a ticker** — type any symbol (NVDA, AAPL, TSLA) and hit Analyse

**2. WebSocket opens** — the browser connects to `/ws/analyse`; the terminal status bar switches to LIVE

**3. Research + Quant run in parallel** (~5–8 s)
   - ResearchAgent fetches 12+ fundamental metrics (P/E, ROE, margins, growth, analyst consensus)
   - QuantAgent computes RSI-14, MACD, Bollinger Bands, SMA 20/50/200 from 1 year of OHLCV
   - Both run concurrently via `asyncio.gather` — neither blocks the other

**4. Bull and Bear agents debate** (~8–12 s each)
   - BullAgent is given all research + quant data and instructed to build the strongest possible bullish case
   - BearAgent receives the same data and builds the strongest possible bear case
   - Both call `anthropic.AsyncAnthropic` directly — no LangChain wrapper, maximum reliability

**5. Decision Engine renders the verdict** (~5–8 s)
   - DecisionAgent weighs both theses against the quantitative signals
   - Forced to make a definitive call — the prompt explicitly rejects hedging
   - Outputs: `BUY/SELL/HOLD`, confidence (30–90%), position size (0–10%), one-sentence rationale citing real numbers

**6. Results stream to the UI in real time** — the Bloomberg-style terminal updates each panel the moment the agent finishes

**Full example outputs:** [EXAMPLES.md](EXAMPLES.md)

---

## ✨ Key Features

- 🧠 **5 specialized AI agents** — Research, Quant, Bull, Bear, Decision; each with a distinct role and dedicated prompt
- ⚡ **Parallel execution** — Research and Quant run simultaneously; total time cut by ~40%
- 📡 **Real-time WebSocket streaming** — watch each agent's output appear live as it completes
- 💹 **Bloomberg-style terminal UI** — dark theme, OHLCV candlestick chart, live status bar, IBM Plex Mono font
- 📈 **Full technical suite** — RSI, MACD, Bollinger Bands, SMA 20/50/200, 52-week range
- 📰 **Multi-source news sentiment** — 4 cascading news sources with rule-based keyword sentiment scoring
- 📊 **12+ fundamental metrics** — P/E, Forward P/E, PEG, P/B, ROE, D/E, margins, revenue growth, analyst consensus
- 💼 **Portfolio tracker** — add analysis results to an in-session positions table with allocation totals
- 🗄️ **Analysis history** — every analysis saved to SQLite; 24-hour cache prevents redundant API calls
- 📉 **Usage analytics** — `/metrics` endpoint: total runs, avg execution time, popular stocks, decision distribution
- 🔄 **Robust fallbacks** — yfinance → Yahoo v8 API → mock fundamentals; 3-attempt retry with User-Agent session
- ✅ **Ticker validation** — invalid symbols rejected before any external call; rate limiting on all endpoints
- 🧪 **27 passing tests** — API endpoints, validation, sentiment scoring, database operations

---

## 📊 Technical Implementation

### Backend

```python
# Parallel data gathering — Research + Quant run concurrently
async def _research_quant_node(self, state):
    research_task = asyncio.create_task(self._research.run(dict(state)))
    quant_task    = asyncio.create_task(self._quant.run(dict(state)))
    research_result, quant_result = await asyncio.gather(research_task, quant_task)
    ...

# Direct Anthropic client — no LangChain wrapper, maximum reliability
client  = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
message = await client.messages.create(
    model="claude-sonnet-4-6", max_tokens=600,
    messages=[{"role": "user", "content": prompt}],
)
```

### Frontend

```jsx
// WebSocket URL derived from window.location — no env vars needed behind nginx
function resolveWsUrl() {
  if (import.meta.env.VITE_WS_URL) return `${import.meta.env.VITE_WS_URL}/ws/analyse`;
  if (window.location.hostname !== "localhost") {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${window.location.host}/ws/analyse`;
  }
  return "ws://localhost:8000/ws/analyse";
}
```

### Persistence

```python
# 24-hour cache — check before running any analysis
cached = get_cached_analysis(ticker)
if cached:
    return {**cached["result"], "_cached": True}
# ... run analysis, then persist
save_analysis(ticker, result, elapsed_ms)
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| 🎨 **Frontend** | React 18 · Vite · TailwindCSS | Bloomberg terminal UI |
| 📡 **Realtime** | WebSocket (native browser API) | Live agent streaming |
| ⚙️ **Backend** | Python 3.11 · FastAPI · Uvicorn | API + WebSocket server |
| 🧠 **Agents** | LangGraph 0.1.14 · LangChain 0.2.6 | Multi-agent pipeline |
| 🤖 **LLM** | Anthropic Claude Sonnet 4.6 (direct API) | Bull/Bear/Decision agents |
| 📊 **Market data** | yfinance 0.2.36 · Yahoo Finance v8 API | OHLCV · fundamentals · news |
| 📈 **Technicals** | ta 0.11.0 (+ pure-pandas fallback) | RSI · MACD · Bollinger · SMA |
| 🗄️ **Persistence** | SQLite (via stdlib `sqlite3`) | Analysis history · cache · metrics |
| 🗄️ **Validation** | Pydantic 2.5.0 | Request/response schemas |
| 🧪 **Testing** | pytest · pytest-asyncio · httpx | 27 tests across API/validation/DB |
| 🚀 **Deployment** | AWS EC2 · Ubuntu 22.04 · nginx · systemd | Production cloud hosting |

---

## 🚀 Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/Likhith252002/ai-hedge-fund.git
cd ai-hedge-fund
echo "ANTHROPIC_API_KEY=sk-ant-..." > backend/.env

# 2. Start the backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# 3. Start the frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** and enter a ticker like `NVDA`, `AAPL`, or `TSLA`.

> 💡 The API key is required for the LLM agents (Bull, Bear, Decision). Without it the pipeline still runs — Research and Quant produce real data, but the theses will be minimal.

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx anyio
pytest -v
```

All 27 tests should pass in under 5 seconds (no network calls, no API key required):

```
tests/test_api.py::test_health                             PASSED
tests/test_api.py::test_health_api_prefix                  PASSED
tests/test_api.py::test_stock_invalid_tickers[TOOLONG]     PASSED
tests/test_api.py::test_metrics_shape                      PASSED
tests/test_api.py::test_history_returns_list               PASSED
...
tests/test_sentiment.py::test_positive_headlines_score_positive[...] PASSED
tests/test_sentiment.py::test_db_save_and_retrieve         PASSED
tests/test_validation.py::test_analysis_request_normalises_ticker PASSED
                                          27 passed in 0.8s
```

---

## 📁 Project Structure

```
ai-hedge-fund/
├── backend/
│   ├── agents/
│   │   ├── research_agent.py   # Fundamentals + news + research_summary
│   │   ├── quant_agent.py      # Technical indicators + quant_signal
│   │   ├── bull_agent.py       # Bullish thesis (Claude Sonnet 4.6)
│   │   ├── bear_agent.py       # Bearish thesis (Claude Sonnet 4.6)
│   │   └── decision_agent.py   # Final verdict (Claude Sonnet 4.6)
│   ├── graph/
│   │   └── hedge_fund_graph.py # LangGraph pipeline — parallel + sequential nodes
│   ├── tools/
│   │   ├── stock_data.py       # yfinance wrapper + v8 API fallback + retry
│   │   └── news_fetcher.py     # 4-source news aggregator + sentiment scorer
│   ├── api/
│   │   ├── main.py             # FastAPI app + CORS + DB init on startup
│   │   └── routes.py           # REST + WS endpoints + validation + rate limiting
│   ├── db/
│   │   └── database.py         # SQLite: save/cache/history/metrics
│   ├── tests/
│   │   ├── test_api.py         # Endpoint tests (health, validation, history)
│   │   ├── test_validation.py  # Ticker regex + Pydantic model tests
│   │   └── test_sentiment.py   # Sentiment scoring + DB integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Root component + WebSocket orchestration
│   │   ├── hooks/
│   │   │   └── useWebSocket.js # WS hook — auto-derives ws:// or wss:// URL
│   │   └── components/
│   │       ├── StockChart.jsx
│   │       ├── AgentStream.jsx
│   │       ├── DecisionCard.jsx
│   │       ├── PortfolioTracker.jsx
│   │       └── TickerInput.jsx
│   └── vite.config.js
├── nginx.conf                  # nginx server block — static + API proxy + WS
├── ai-hedge-fund.service       # systemd unit (uvicorn, auto-restart)
├── deploy.sh                   # One-command redeploy script
├── ARCHITECTURE.md             # Technical deep-dive
├── EXAMPLES.md                 # Real analysis walkthroughs (NVDA, META, PYPL)
├── DEPLOYMENT.md               # EC2 deployment reference
├── EC2_SETUP.md                # Fresh EC2 setup walkthrough
├── render.yaml                 # Render.com deploy config (alternative)
└── docker-compose.yml
```

---

## 🌐 Deployment

### Production — AWS EC2

| Component | Details |
|:---|:---|
| Instance | AWS EC2 t2.micro · Ubuntu 22.04 LTS |
| Web server | nginx — static files + `/api/*` and `/ws/*` reverse proxy |
| Backend | uvicorn managed by systemd (`ai-hedge-fund.service`) |
| Frontend | React/Vite build served from `/var/www/ai-hedge-fund` |
| URL | [http://18.224.16.180](http://18.224.16.180) |

**Redeploy after pushing changes:**

```bash
ssh -i your-key.pem ubuntu@18.224.16.180
cd /home/ubuntu/ai-hedge-fund && bash deploy.sh
```

Full setup walkthrough: [EC2_SETUP.md](EC2_SETUP.md) · Deployment reference: [DEPLOYMENT.md](DEPLOYMENT.md)

### Deploy with Docker

```bash
docker-compose up --build
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## ⚠️ Disclaimer

> This project is **for educational and research purposes only**. It is **not financial advice**. The agents' outputs are experimental and should never be used to make real investment decisions. Always consult a licensed financial advisor.

---

## 📄 License

MIT © [Likhith Thondamanati](https://github.com/Likhith252002) 2026 — see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Likhith Thondamanati](https://github.com/Likhith252002)

</div>
