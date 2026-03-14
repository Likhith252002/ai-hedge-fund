"""
bull_agent.py
Constructs the bullish investment thesis using research + quant data.
Uses Claude LLM to generate a structured bull case.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BULL_PROMPT = """You are an optimistic equity analyst building a BULL case.

Ticker: {ticker}
Research summary: {research_summary}
Quant signal: {quant_signal}

Technical indicators:
  RSI-14: {rsi_14}  |  MACD: {macd}  |  MACD signal: {macd_signal}
  SMA-20: {sma_20}  |  SMA-50: {sma_50}  |  SMA-200: {sma_200}
  52w-high distance: {price_vs_52w_high}%  |  52w-low distance: {price_vs_52w_low}%

Fundamentals:
  P/E: {pe_ratio}  |  Forward P/E: {forward_pe}  |  P/B: {price_to_book}
  ROE: {roe}  |  Revenue growth: {revenue_growth}  |  Profit margin: {profit_margin}
  Analyst target: {analyst_target}  |  Recommendation: {recommendation_mean}

Recent news:
{news_headlines}

Write a concise bull thesis (3-5 bullet points) covering:
- Growth catalysts
- Valuation upside
- Technical momentum
- Positive news drivers

Be specific. Reference the numbers above where relevant.
"""


class BullAgent:
    def __init__(self, llm=None):
        self.llm = llm

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("BullAgent: building bull thesis for %s", ticker)

        news_headlines = "\n".join(
            f"- {n['title']}" for n in state.get("news", [])[:5]
        )

        ind  = state.get("indicators", {})
        fund = state.get("fundamentals", {})

        def _pct(v):
            return f"{v*100:.1f}%" if v is not None else "N/A"

        if self.llm:
            from langchain_core.messages import HumanMessage
            prompt = BULL_PROMPT.format(
                ticker              = ticker,
                research_summary    = state.get("research_summary", ""),
                quant_signal        = state.get("quant_signal", "NEUTRAL"),
                rsi_14              = ind.get("rsi_14", "N/A"),
                macd                = ind.get("macd", "N/A"),
                macd_signal         = ind.get("macd_signal", "N/A"),
                sma_20              = ind.get("sma_20", "N/A"),
                sma_50              = ind.get("sma_50", "N/A"),
                sma_200             = ind.get("sma_200", "N/A"),
                price_vs_52w_high   = ind.get("price_vs_52w_high", "N/A"),
                price_vs_52w_low    = ind.get("price_vs_52w_low", "N/A"),
                pe_ratio            = fund.get("pe_ratio", "N/A"),
                forward_pe          = fund.get("forward_pe", "N/A"),
                price_to_book       = fund.get("price_to_book", "N/A"),
                roe                 = _pct(fund.get("roe")),
                revenue_growth      = _pct(fund.get("revenue_growth")),
                profit_margin       = _pct(fund.get("profit_margin")),
                analyst_target      = fund.get("analyst_target", "N/A"),
                recommendation_mean = fund.get("recommendation_mean", "N/A"),
                news_headlines      = news_headlines,
            )
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            bull_thesis = response.content
        else:
            rsi    = ind.get("rsi_14", 50)
            sma_20 = ind.get("sma_20", 0)
            sma_50 = ind.get("sma_50", 0)
            pe     = fund.get("pe_ratio", "N/A")
            rev_g  = _pct(fund.get("revenue_growth"))
            bull_thesis = (
                f"• Quant signal: {state.get('quant_signal', 'NEUTRAL')} "
                f"(RSI={rsi:.1f}, SMA20={'>' if sma_20 > sma_50 else '<'}SMA50)\n"
                f"• P/E ratio: {pe} — {'attractive valuation' if isinstance(pe, (int,float)) and pe < 25 else 'growth premium justified by fundamentals'}\n"
                f"• Revenue growth: {rev_g} — positive top-line momentum\n"
                f"• Technical indicators suggest {'upward' if state.get('quant_signal') == 'BUY' else 'stabilising'} momentum\n"
                f"• Sector tailwinds support continued outperformance for {ticker}"
            )

        state["bull_thesis"] = bull_thesis
        logger.info("BullAgent: thesis generated for %s", ticker)
        return state
