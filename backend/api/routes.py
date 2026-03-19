"""
routes.py
REST API and WebSocket endpoints for the AI Hedge Fund.

Endpoints:
  GET  /health                     — liveness probe
  GET  /metrics                    — usage analytics
  GET  /api/v1/stock/{ticker}      — fundamentals + OHLCV
  GET  /api/v1/news/{ticker}       — recent news headlines
  POST /api/v1/analyse             — full analysis (REST, cached)
  GET  /api/v1/history             — recent analyses
  GET  /api/v1/history/{id}        — single analysis by id
  WS   /ws/analyse                 — streaming real-time analysis
"""

from __future__ import annotations

import logging
import os
import re
import time
from collections import defaultdict

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Ticker validation ─────────────────────────────────────────────────────────

_TICKER_RE = re.compile(r"^[A-Z]{1,5}$")


def _validate_ticker(ticker: str) -> str:
    t = ticker.strip().upper()
    if not _TICKER_RE.match(t):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid ticker '{ticker}'. "
                "Tickers must be 1–5 uppercase letters (e.g. NVDA, AAPL, TSLA)."
            ),
        )
    return t


# ── Simple in-process rate limiter ────────────────────────────────────────────

_rate_store: dict = defaultdict(list)
_RATE_WINDOW       = 60   # seconds
_RATE_MAX_ANALYSE  = 5    # analysis requests per window per IP
_RATE_MAX_DATA     = 30   # data requests per window per IP


def _check_rate(client_ip: str, limit: int) -> None:
    now    = time.time()
    cutoff = now - _RATE_WINDOW
    _rate_store[client_ip] = [t for t in _rate_store[client_ip] if t > cutoff]
    if len(_rate_store[client_ip]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {limit} requests per {_RATE_WINDOW}s. Please wait.",
        )
    _rate_store[client_ip].append(now)


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", tags=["system"])
@router.get("/api/health", tags=["system"])
async def health():
    """Liveness probe — returns 200 when the service is up."""
    return {"status": "ok", "service": "ai-hedge-fund"}


# ── Metrics ───────────────────────────────────────────────────────────────────

@router.get("/metrics", tags=["system"])
@router.get("/api/metrics", tags=["system"])
async def metrics():
    """
    Usage analytics:
      - Total analyses run
      - Average execution time
      - Most analysed stocks
      - BUY / SELL / HOLD distribution
    """
    from db.database import get_metrics
    return get_metrics()


# ── Stock data ────────────────────────────────────────────────────────────────

@router.get("/api/v1/stock/{ticker}", tags=["stock"])
async def get_stock(ticker: str, request: Request):
    """Return fundamentals + OHLCV chart data for a ticker."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate(client_ip, _RATE_MAX_DATA)
    ticker = _validate_ticker(ticker)

    from tools.stock_data import get_fundamentals, get_ohlcv_list
    fundamentals = get_fundamentals(ticker)
    ohlcv        = get_ohlcv_list(ticker, period="3mo")
    return {"fundamentals": fundamentals, "ohlcv": ohlcv}


@router.get("/api/v1/news/{ticker}", tags=["news"])
async def get_news(ticker: str, request: Request):
    """Return recent news headlines with sentiment scores for a ticker."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate(client_ip, _RATE_MAX_DATA)
    ticker = _validate_ticker(ticker)

    from tools.news_fetcher import get_news as fetch_news
    news = fetch_news(ticker)
    return {"ticker": ticker, "news": news}


# ── REST analysis (cached) ────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    ticker:    str
    use_llm:   bool = True
    use_cache: bool = True

    @field_validator("ticker")
    @classmethod
    def ticker_must_be_valid(cls, v: str) -> str:
        t = v.strip().upper()
        if not _TICKER_RE.match(t):
            raise ValueError(
                f"Invalid ticker '{v}'. Must be 1–5 letters (e.g. NVDA, AAPL)."
            )
        return t


@router.post("/api/v1/analyse", tags=["analysis"])
async def analyse(body: AnalysisRequest, request: Request):
    """
    Run full multi-agent analysis for a ticker.
    Results are cached for 24 h — pass use_cache=false to force a fresh run.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate(client_ip, _RATE_MAX_ANALYSE)

    from db.database import get_cached_analysis, save_analysis
    from graph.hedge_fund_graph import HedgeFundGraph

    ticker = body.ticker

    if body.use_cache:
        cached = get_cached_analysis(ticker)
        if cached:
            logger.info("Cache hit for %s (id=%s)", ticker, cached["id"])
            return {**cached["result"], "_cached": True, "_cache_id": cached["id"]}

    start_ms = int(time.time() * 1000)
    graph    = HedgeFundGraph(llm=None)
    result   = await graph.run(ticker)
    elapsed  = int(time.time() * 1000) - start_ms

    save_analysis(ticker, result, elapsed)
    return {**result, "_cached": False, "_execution_time_ms": elapsed}


# ── Analysis history ──────────────────────────────────────────────────────────

@router.get("/api/v1/history", tags=["history"])
async def get_history(limit: int = 20):
    """Return the most recent completed analyses (summary, no full JSON)."""
    if limit < 1 or limit > 100:
        raise HTTPException(400, "limit must be between 1 and 100")
    from db.database import get_recent_analyses
    return {"analyses": get_recent_analyses(limit)}


@router.get("/api/v1/history/{analysis_id}", tags=["history"])
async def get_history_item(analysis_id: int):
    """Return a single past analysis including the full result."""
    from db.database import get_analysis_by_id
    item = get_analysis_by_id(analysis_id)
    if not item:
        raise HTTPException(404, f"Analysis {analysis_id} not found")
    return item


# ── WebSocket streaming analysis ──────────────────────────────────────────────

_NODE_LABELS = {
    "research_quant": "Research & Quant",
    "bull":           "Bull Agent",
    "bear":           "Bear Agent",
    "decide":         "Decision Agent",
}
_NODE_KEYS = {
    "research_quant": ["research_summary", "quant_signal", "indicators", "fundamentals", "news"],
    "bull":           ["bull_thesis"],
    "bear":           ["bear_thesis"],
    "decide":         ["decision"],
}


@router.websocket("/ws/analyse")
async def ws_analyse(websocket: WebSocket):
    """
    Real-time streaming analysis via WebSocket.

    Client sends:  {"ticker": "TSLA", "use_llm": true}
    Server emits one message per agent as it completes, then a final "complete".
    """
    await websocket.accept()
    start_ms = int(time.time() * 1000)

    try:
        data       = await websocket.receive_json()
        raw_ticker = data.get("ticker", "").strip()

        if not raw_ticker:
            await websocket.send_json({"event": "error", "message": "ticker is required"})
            return

        if not _TICKER_RE.match(raw_ticker.upper()):
            await websocket.send_json({
                "event":   "error",
                "message": (
                    f"Invalid ticker '{raw_ticker}'. "
                    "Must be 1–5 letters (e.g. NVDA, AAPL, TSLA)."
                ),
            })
            return

        ticker = raw_ticker.upper()

        from db.database import save_analysis
        from graph.hedge_fund_graph import HedgeFundGraph

        graph       = HedgeFundGraph(llm=None)
        final_state: dict = {"ticker": ticker}

        async for chunk in graph.stream(ticker):
            node_name  = chunk["node"]
            node_state = chunk["state"]
            final_state.update(node_state)

            keys    = _NODE_KEYS.get(node_name, [])
            payload = {k: node_state.get(k) for k in keys if k in node_state}

            await websocket.send_json({
                "event": "agent_complete",
                "agent": node_name,
                "label": _NODE_LABELS.get(node_name, node_name),
                **payload,
            })

        elapsed = int(time.time() * 1000) - start_ms
        await websocket.send_json({"event": "complete", "result": final_state})

        try:
            save_analysis(ticker, final_state, elapsed)
        except Exception as db_exc:
            logger.warning("DB write failed for %s: %s", ticker, db_exc)

    except WebSocketDisconnect:
        logger.info("ws_analyse: client disconnected")
    except Exception as exc:
        logger.exception("ws_analyse error: %s", exc)
        try:
            await websocket.send_json({"event": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
