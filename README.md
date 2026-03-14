# AI Hedge Fund

A production-grade, multi-agent AI investment analysis platform powered by **LangGraph**, **Claude (Anthropic)**, and **real-time market data**.

> **GitHub:** https://github.com/Likhith252002/ai-hedge-fund

---

## Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                        AI HEDGE FUND                             ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ┌──────────────────────────────────────────────────────────┐   ║
║  │            REACT FRONTEND  (Vite · port 5173)            │   ║
║  │                                                          │   ║
║  │  TickerInput → StockChart  DecisionCard  PortfolioTrack  │   ║
║  │                   AgentStream (Bull/Bear/Quant/Research)  │   ║
║  └────────────────────────┬─────────────────────────────────┘   ║
║                           │  REST API                           ║
║  ┌────────────────────────▼─────────────────────────────────┐   ║
║  │            FASTAPI BACKEND  (Uvicorn · port 8000)        │   ║
║  │                                                          │   ║
║  │  POST /api/v1/analyse                                    │   ║
║  │  GET  /api/v1/stock/{ticker}                             │   ║
║  │  GET  /api/v1/news/{ticker}                              │   ║
║  │                                                          │   ║
║  │  ╔════════════════════════════════════════════════════╗  │   ║
║  │  ║         LANGGRAPH PIPELINE                        ║  │   ║
║  │  ║                                                   ║  │   ║
║  │  ║  ResearchAgent → QuantAgent → BullAgent  ──┐      ║  │   ║
║  │  ║                            → BearAgent  ──┼─► DecisionAgent ║
║  │  ╚═══════════════════════════════════════════╪════════╝  │   ║
║  │                                              │           │   ║
║  │  ┌─ Tools ─────────────────────────────────┐ │           │   ║
║  │  │  yfinance · ta · BeautifulSoup · Claude │ │           │   ║
║  │  └─────────────────────────────────────────┘ │           │   ║
║  └──────────────────────────────────────────────┘           │   ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 · Vite · TailwindCSS · Chart.js |
| Backend | Python 3.11 · FastAPI · Uvicorn |
| Agents | LangGraph · LangChain · Claude (Anthropic) |
| Market Data | yfinance · ta (technical analysis) |
| News | yfinance news · BeautifulSoup |
| Infra | Docker · Railway |

---

## Quick Start

### 1. Clone & configure
```bash
git clone https://github.com/Likhith252002/ai-hedge-fund.git
cd ai-hedge-fund
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### 2. Run backend
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### 3. Run frontend
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**, enter a ticker (e.g. `AAPL`), and click **Analyse**.

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/api/v1/analyse` | POST | Run full multi-agent analysis |
| `/api/v1/stock/{ticker}` | GET | Fundamentals + OHLCV data |
| `/api/v1/news/{ticker}` | GET | Recent news headlines |

---

## Agents

| Agent | Role |
|---|---|
| **ResearchAgent** | Fetches fundamentals, news, key ratios |
| **QuantAgent** | Computes RSI, MACD, Bollinger Bands, SMA signals |
| **BullAgent** | Builds bullish thesis using Claude LLM |
| **BearAgent** | Builds bearish thesis using Claude LLM |
| **DecisionAgent** | Synthesises all inputs → BUY / SELL / HOLD + confidence |
