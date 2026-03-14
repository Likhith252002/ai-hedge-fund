"""
routes.py
REST API endpoints for the AI Hedge Fund.
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Health ──────────────────────────────────────────────────────────────────

@router.get("/health", tags=["system"])
@router.get("/api/health", tags=["system"])
async def health():
    return {"status": "ok", "service": "ai-hedge-fund"}


# ── Analysis ────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    ticker: str
    use_llm: bool = True


@router.post("/api/v1/analyse", tags=["analysis"])
async def analyse(body: AnalysisRequest):
    """Run full multi-agent analysis for a ticker. Returns the complete state."""
    from graph.hedge_fund_graph import HedgeFundGraph

    llm = None
    if body.use_llm and os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.3)

    graph  = HedgeFundGraph(llm=llm)
    result = await graph.run(body.ticker)
    return result


# ── Stock data ───────────────────────────────────────────────────────────────

@router.get("/api/v1/stock/{ticker}", tags=["stock"])
async def get_stock(ticker: str):
    """Return fundamentals + OHLCV chart data for a ticker."""
    from tools.stock_data import get_fundamentals, get_ohlcv_list
    fundamentals = get_fundamentals(ticker.upper())
    ohlcv        = get_ohlcv_list(ticker.upper(), period="3mo")
    return {"fundamentals": fundamentals, "ohlcv": ohlcv}


@router.get("/api/v1/news/{ticker}", tags=["news"])
async def get_news(ticker: str):
    """Return recent news for a ticker."""
    from tools.news_fetcher import get_news as fetch_news
    news = fetch_news(ticker.upper())
    return {"ticker": ticker.upper(), "news": news}


# ── WebSocket streaming analysis ─────────────────────────────────────────────

# Maps internal LangGraph node names → human-readable labels sent to the client
_NODE_LABELS = {
    "research_quant": "Research & Quant",
    "bull":           "Bull Agent",
    "bear":           "Bear Agent",
    "decide":         "Decision Agent",
}

# Keys each node contributes to the streamed payload
_NODE_KEYS = {
    "research_quant": ["research_summary", "quant_signal", "indicators", "fundamentals", "news"],
    "bull":           ["bull_thesis"],
    "bear":           ["bear_thesis"],
    "decide":         ["decision"],
}


@router.websocket("/ws/analyse")
async def ws_analyse(websocket: WebSocket):
    """
    WebSocket endpoint that streams agent progress in real-time.

    Client sends:  {"ticker": "TSLA", "use_llm": false}
    Server emits:
      {"event": "agent_complete", "agent": "research_quant", "label": "Research & Quant", ...data}
      {"event": "agent_complete", "agent": "bull",  "label": "Bull Agent",  ...data}
      {"event": "agent_complete", "agent": "bear",  "label": "Bear Agent",  ...data}
      {"event": "agent_complete", "agent": "decide","label": "Decision Agent", ...data}
      {"event": "complete", "result": { ...full final state... }}
    On error:
      {"event": "error", "message": "..."}
    """
    await websocket.accept()
    try:
        data    = await websocket.receive_json()
        ticker  = data.get("ticker", "").strip().upper()
        use_llm = data.get("use_llm", True)

        if not ticker:
            await websocket.send_json({"event": "error", "message": "ticker is required"})
            return

        # Optionally wire up LLM
        llm = None
        if use_llm and os.getenv("ANTHROPIC_API_KEY"):
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.3)

        from graph.hedge_fund_graph import HedgeFundGraph
        graph = HedgeFundGraph(llm=llm)

        # Accumulate full state so we can send "complete" at the end
        final_state: dict = {"ticker": ticker}

        async for chunk in graph.stream(ticker):
            node_name  = chunk["node"]
            node_state = chunk["state"]
            final_state.update(node_state)

            # Extract only the keys this node produced
            keys    = _NODE_KEYS.get(node_name, [])
            payload = {k: node_state.get(k) for k in keys if k in node_state}

            await websocket.send_json({
                "event": "agent_complete",
                "agent": node_name,
                "label": _NODE_LABELS.get(node_name, node_name),
                **payload,
            })

        await websocket.send_json({"event": "complete", "result": final_state})

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
