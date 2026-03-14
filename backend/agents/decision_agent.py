"""
decision_agent.py
Synthesises bull + bear theses and quant signals into a final
investment decision with confidence score and position sizing.
Always calls the Claude LLM — never uses rule-based fallback.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

DECISION_PROMPT = """You are a senior portfolio manager making a final investment decision.

Ticker: {ticker}
Current price: ${current_price}

Key indicators:
  RSI-14: {rsi_14}  |  MACD: {macd}  |  SMA20 vs SMA50: {sma_cross}
  52w-high distance: {price_vs_52w_high}%

Key fundamentals:
  P/E: {pe_ratio}  |  Forward P/E: {forward_pe}  |  ROE: {roe}
  Revenue growth: {revenue_growth}  |  Analyst target: ${analyst_target}

QUANT SIGNAL: {quant_signal}

BULL THESIS:
{bull_thesis}

BEAR THESIS:
{bear_thesis}

Based on all of the above, provide:
1. Decision: BUY / SELL / HOLD
2. Confidence: 0-100%
3. Suggested position size: 0-10% of portfolio
4. One-sentence rationale

Format your response as:
DECISION: <BUY|SELL|HOLD>
CONFIDENCE: <0-100>
POSITION_SIZE: <0-10>
RATIONALE: <one sentence>
"""


class DecisionAgent:
    def __init__(self, llm=None):
        self.llm = llm

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("DecisionAgent: synthesising decision for %s", ticker)

        ind  = state.get("indicators", {})
        fund = state.get("fundamentals", {})

        # current_price comes from fundamentals (StockDataTool.get_fundamentals doesn't
        # include it), so fetch it fresh — or fall back to analyst_target as proxy.
        from tools.stock_data import StockDataTool
        price_data    = StockDataTool().get_current_price(ticker)
        current_price = price_data.get("price", 0)

        def _pct(v):
            return f"{v*100:.1f}%" if v is not None else "N/A"

        sma_20 = ind.get("sma_20", 0)
        sma_50 = ind.get("sma_50", 0)
        sma_cross = f"{sma_20:.2f} {'>' if sma_20 > sma_50 else '<'} {sma_50:.2f}"

        # Always use Claude — prefer injected llm, otherwise build one from env
        llm = self.llm
        if llm is None:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is not set. DecisionAgent requires the Claude API."
                )
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model="claude-sonnet-4-6",
                temperature=0.3,
                anthropic_api_key=api_key,
            )

        from langchain_core.messages import HumanMessage
        prompt = DECISION_PROMPT.format(
            ticker              = ticker,
            current_price       = current_price,
            rsi_14              = ind.get("rsi_14", "N/A"),
            macd                = ind.get("macd", "N/A"),
            sma_cross           = sma_cross,
            price_vs_52w_high   = ind.get("price_vs_52w_high", "N/A"),
            pe_ratio            = fund.get("pe_ratio", "N/A"),
            forward_pe          = fund.get("forward_pe", "N/A"),
            roe                 = _pct(fund.get("roe")),
            revenue_growth      = _pct(fund.get("revenue_growth")),
            analyst_target      = fund.get("analyst_target", "N/A"),
            bull_thesis         = state.get("bull_thesis", ""),
            bear_thesis         = state.get("bear_thesis", ""),
            quant_signal        = state.get("quant_signal", "NEUTRAL"),
        )
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        decision = _parse_decision(response.content)
        decision["current_price"] = current_price

        state["decision"] = decision
        logger.info(
            "DecisionAgent: %s — action=%s confidence=%s%%",
            ticker, decision["action"], decision["confidence"]
        )
        return state


def _parse_decision(raw: str) -> Dict[str, Any]:
    lines = {
        line.split(":")[0].strip(): line.split(":", 1)[1].strip()
        for line in raw.splitlines()
        if ":" in line
    }
    return {
        "action":        lines.get("DECISION", "HOLD"),
        "confidence":    int(lines.get("CONFIDENCE", "50").replace("%", "")),
        "position_size": float(lines.get("POSITION_SIZE", "0").replace("%", "")),
        "rationale":     lines.get("RATIONALE", "Insufficient data for decision."),
    }
