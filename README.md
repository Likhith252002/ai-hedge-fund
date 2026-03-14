<div align="center">

```
 █████╗ ██╗    ██╗  ██╗███████╗██████╗  ██████╗ ███████╗    ███████╗██╗   ██╗███╗   ██╗██████╗
██╔══██╗██║    ██║  ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝    ██╔════╝██║   ██║████╗  ██║██╔══██╗
███████║██║    ███████║█████╗  ██║  ██║██║  ███╗█████╗      █████╗  ██║   ██║██╔██╗ ██║██║  ██║
██╔══██║██║    ██╔══██║██╔══╝  ██║  ██║██║   ██║██╔══╝      ██╔══╝  ██║   ██║██║╚██╗██║██║  ██║
██║  ██║██║    ██║  ██║███████╗██████╔╝╚██████╔╝███████╗    ██║     ╚██████╔╝██║ ╚████║██████╔╝
╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚═════╝
```

### 🤖 5 AI agents debate Wall Street in real time

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1.14-FF6B35?style=for-the-badge&logo=chainlink&logoColor=white)](https://langchain-ai.github.io/langgraph)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)
[![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<br/>

**[🚀 Live Demo](https://ai-hedge-fund-frontend-0ega.onrender.com)** &nbsp;•&nbsp;
**[📖 Docs](#how-it-works)** &nbsp;•&nbsp;
**[🐛 Report Bug](https://github.com/Likhith252002/ai-hedge-fund/issues)** &nbsp;•&nbsp;
**[✨ Request Feature](https://github.com/Likhith252002/ai-hedge-fund/issues)**

<br/>

> 🤖 Multi-agent AI system that analyzes stocks using 5 specialized LLM agents — Research, Quant, Bull, Bear & Decision — with real-time WebSocket streaming and a Bloomberg-style terminal UI

</div>

---

## 🎬 Demo

<div align="center">

### 🌐 [https://ai-hedge-fund-frontend-0ega.onrender.com](https://ai-hedge-fund-frontend-0ega.onrender.com)

> Enter any ticker (e.g. `NVDA`, `AAPL`, `TSLA`) and watch 5 AI agents debate the stock live.

![Demo](https://raw.githubusercontent.com/Likhith252002/ai-hedge-fund/main/docs/demo.gif)

*↑ Bloomberg-style terminal — real-time agent streaming*

</div>

---

## ⚡ Performance

<div align="center">

| Metric | Value |
|:---|:---:|
| ⏱️ Analysis time | ~30 seconds |
| 🤖 Agents running | 5 specialized LLMs |
| ⚡ Execution | Parallel agent pipeline |
| 📡 Streaming | Real-time WebSocket |
| 📊 Data points | 12+ fundamental metrics |
| 📈 Indicators | RSI, MACD, Bollinger, SMA 20/50/200 |

</div>

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│              Bloomberg Terminal UI  (React + Vite)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │  WebSocket  /ws/analyse
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND  (Uvicorn)                    │
│                                                                 │
│   REST  /api/v1/stock/{ticker}   /api/v1/news/{ticker}         │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                  LANGGRAPH PIPELINE                     │  │
│   │                                                         │  │
│   │   ┌─────────────────┐   ┌─────────────────┐            │  │
│   │   │  Research Agent  │   │   Quant Agent    │  ← parallel │  │
│   │   │  fundamentals   │   │  RSI·MACD·BB    │            │  │
│   │   └────────┬────────┘   └────────┬────────┘            │  │
│   │            └──────────┬──────────┘                      │  │
│   │                       ▼                                 │  │
│   │          ┌────────────────────────┐                     │  │
│   │          │  ┌──────┐  ┌────────┐  │  ← parallel         │  │
│   │          │  │ Bull │  │  Bear  │  │                     │  │
│   │          │  │Agent │  │ Agent  │  │                     │  │
│   │          │  └──────┘  └────────┘  │                     │  │
│   │          └────────────┬───────────┘                     │  │
│   │                       ▼                                 │  │
│   │              ┌─────────────────┐                        │  │
│   │              │ Decision Engine │                        │  │
│   │              │ BUY/SELL/HOLD + │                        │  │
│   │              │   confidence    │                        │  │
│   │              └─────────────────┘                        │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
    ┌─────────▼──────────┐    ┌──────────▼──────────┐
    │    yfinance API    │    │   Anthropic Claude   │
    │  OHLCV · Fundamentals   │  claude-sonnet-4-6   │
    └────────────────────┘    └─────────────────────┘
```

---

## 🤖 How It Works

**1. 📥 You enter a ticker symbol** (e.g. `NVDA`)

**2. 📡 WebSocket connection opens** — the browser connects directly to the FastAPI backend over a persistent WebSocket, enabling real-time streaming

**3. 🔬 Research & Quant agents run in parallel** — simultaneously fetching 12+ fundamental metrics (P/E, ROE, margins, growth) and computing 10+ technical indicators (RSI-14, MACD, Bollinger Bands, SMA 20/50/200)

**4. 🐂🐻 Bull & Bear agents debate** — two Claude LLM instances independently build the strongest possible bullish and bearish cases using all gathered data

**5. ⚖️ Decision Engine renders the verdict** — a final Claude agent weighs both theses and outputs a structured `BUY / SELL / HOLD` decision with confidence score and position sizing recommendation

---

## 🧠 The Agents

| Agent | Role | Output |
|:---|:---|:---|
| 🔬 **Research Agent** | Fetches live fundamentals, news sentiment, key ratios from yfinance | `research_summary`, `fundamentals`, `news` |
| 📊 **Quant Agent** | Computes RSI-14, MACD, Bollinger Bands, SMA 20/50/200, 52-week range | `quant_signal`, `indicators` |
| 🐂 **Bull Agent** | Builds the strongest bullish thesis using Claude LLM | `bull_thesis` |
| 🐻 **Bear Agent** | Builds the strongest bearish thesis using Claude LLM | `bear_thesis` |
| ⚖️ **Decision Agent** | Synthesises all inputs → final investment verdict | `decision` (action, confidence, position_size) |

---

## ✨ Key Features

- 🧠 **5 Specialized AI Agents** — each with a distinct role in the investment pipeline
- ⚡ **Parallel Execution** — Research+Quant run simultaneously, then Bull+Bear run simultaneously
- 📡 **Real-time WebSocket Streaming** — watch each agent complete live in the terminal UI
- 💹 **Bloomberg Terminal UI** — dark theme, OHLCV candlestick chart, live status bar
- 📈 **Technical Analysis** — RSI, MACD, Bollinger Bands, SMA 20/50/200 via the `ta` library
- 📰 **News Sentiment** — live news headlines scored with financial keyword analysis
- 📊 **12+ Fundamental Metrics** — P/E, Forward P/E, PEG, P/B, ROE, D/E, margins, growth
- 💼 **Portfolio Tracker** — add analysis results to a watchlist
- 🔄 **Retry + Fallback** — 3-attempt retry on yfinance rate limits with graceful fallback
- 🚀 **One-command deploy** — `render.yaml` for instant Render.com deployment

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|:---|:---|:---|
| 🎨 **Frontend** | React 18 · Vite · TailwindCSS | Bloomberg terminal UI |
| 📡 **Realtime** | WebSocket (native browser API) | Live agent streaming |
| ⚙️ **Backend** | Python 3.11 · FastAPI · Uvicorn | API + WebSocket server |
| 🧠 **Agents** | LangGraph 0.1.14 · LangChain 0.2.6 | Multi-agent orchestration |
| 🤖 **LLM** | Anthropic Claude (claude-sonnet-4-6) | Bull/Bear/Decision agents |
| 📊 **Market Data** | yfinance 0.2.36 | OHLCV · fundamentals · news |
| 📈 **Technicals** | ta 0.11.0 | RSI · MACD · Bollinger · SMA |
| 🗄️ **Validation** | Pydantic 2.5.0 | Request/response schemas |
| 🚀 **Deployment** | Render.com | Free-tier cloud hosting |

---

## 🚀 Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/Likhith252002/ai-hedge-fund.git
cd ai-hedge-fund
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Start the backend
cd backend && pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# 3. Start the frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173**, type a ticker like `NVDA` or `AAPL`, and hit **Analyse**.

> 💡 The app works without an `ANTHROPIC_API_KEY` — agents will run in rule-based mode instead of LLM mode.

---

## 📁 Project Structure

```
ai-hedge-fund/
├── backend/
│   ├── agents/
│   │   ├── research_agent.py   # Fundamentals + news
│   │   ├── quant_agent.py      # Technical indicators
│   │   ├── bull_agent.py       # Bullish thesis (Claude)
│   │   ├── bear_agent.py       # Bearish thesis (Claude)
│   │   └── decision_agent.py   # Final verdict (Claude)
│   ├── graph/
│   │   └── hedge_fund_graph.py # LangGraph pipeline wiring
│   ├── tools/
│   │   ├── stock_data.py       # yfinance wrapper + retry
│   │   └── news_fetcher.py     # News + sentiment scoring
│   ├── api/
│   │   ├── main.py             # FastAPI app + CORS
│   │   └── routes.py           # REST + WebSocket endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Root component + WS logic
│   │   ├── hooks/
│   │   │   └── useWebSocket.js # WebSocket hook
│   │   └── components/
│   │       ├── StockChart.jsx
│   │       ├── AgentStream.jsx
│   │       ├── DecisionCard.jsx
│   │       ├── PortfolioTracker.jsx
│   │       └── TickerInput.jsx
│   └── vite.config.js
├── render.yaml                 # One-click Render deploy
└── docker-compose.yml
```

---

## 🌐 Deployment

### Deploy to Render (recommended)

The repo includes a `render.yaml` — import the repo in [Render](https://render.com) and it will configure both services automatically.

**Environment variables to set in Render dashboard:**

| Service | Variable | Value |
|:---|:---|:---|
| Backend | `ANTHROPIC_API_KEY` | Your Anthropic API key |
| Frontend | `VITE_API_URL` | `https://your-backend.onrender.com` |
| Frontend | `VITE_WS_URL` | `wss://your-backend.onrender.com` |

### Deploy with Docker

```bash
docker-compose up --build
```

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## ⚠️ Disclaimer

> This project is **for educational and research purposes only**. It is **not financial advice**. The AI agents' outputs are experimental and should never be used to make real investment decisions. Always consult a licensed financial advisor before investing.

---

## 📄 License

MIT © [Likhith Thondamanati](https://github.com/Likhith252002) 2026 — see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ by [Likhith Thondamanati](https://github.com/Likhith252002)

</div>
