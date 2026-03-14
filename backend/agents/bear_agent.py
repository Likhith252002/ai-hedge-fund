"""
bear_agent.py
Constructs the bearish investment thesis using research + quant data.
Uses Claude LLM to generate a structured bear case.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

BEAR_PROMPT = """You are a skeptical equity analyst building a BEAR case.

Ticker: {ticker}
Research summary: {research_summary}
Quant signal: {quant_signal}

Technical indicators:
  RSI-14: {rsi_14}  |  MACD: {macd}  |  MACD signal: {macd_signal}
  SMA-20: {sma_20}  |  SMA-50: {sma_50}  |  SMA-200: {sma_200}
  52w-high distance: {price_vs_52w_high}%  |  52w-low distance: {price_vs_52w_low}%

Fundamentals:
  P/E: {pe_ratio}  |  Forward P/E: {forward_pe}  |  P/B: {price_to_book}
  Debt/Equity: {debt_to_equity}  |  Revenue growth: {revenue_growth}  |  Profit margin: {profit_margin}
  Analyst target: {analyst_target}  |  Recommendation: {recommendation_mean}

Recent news:
{news_headlines}

Write a concise bear thesis (3-5 bullet points) covering:
- Key risks and headwinds
- Valuation concerns or overextension
- Technical weakness signals
- Negative news drivers or macro risks

Be specific. Reference the numbers above where relevant.
"""


class BearAgent:
    def __init__(self, llm=None):
        self.llm = llm

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("BearAgent: building bear thesis for %s", ticker)

        news_headlines = "\n".join(
            f"- {n['title']}" for n in state.get("news", [])[:5]
        )

        ind  = state.get("indicators", {})
        fund = state.get("fundamentals", {})

        def _pct(v):
            return f"{v*100:.1f}%" if v is not None else "N/A"

        if self.llm:
            from langchain_core.messages import HumanMessage
            prompt = BEAR_PROMPT.format(
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
                debt_to_equity      = fund.get("debt_to_equity", "N/A"),
                revenue_growth      = _pct(fund.get("revenue_growth")),
                profit_margin       = _pct(fund.get("profit_margin")),
                analyst_target      = fund.get("analyst_target", "N/A"),
                recommendation_mean = fund.get("recommendation_mean", "N/A"),
                news_headlines      = news_headlines,
            )
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            bear_thesis = response.content
        else:
            rsi    = ind.get("rsi_14", 50)
            sma_20 = ind.get("sma_20", 0)
            sma_50 = ind.get("sma_50", 0)
            pe     = fund.get("pe_ratio", "N/A")
            dte    = fund.get("debt_to_equity", "N/A")
            rev_g  = _pct(fund.get("revenue_growth"))
            bear_thesis = (
                f"• Quant signal: {state.get('quant_signal', 'NEUTRAL')} "
                f"(RSI={rsi:.1f}, SMA20={'>' if sma_20 > sma_50 else '<'}SMA50 — "
                f"{'potential overextension' if rsi > 65 else 'momentum weakening'})\n"
                f"• P/E ratio: {pe} — {'elevated vs historical norms' if isinstance(pe, (int,float)) and pe > 25 else 'valuation risk if growth slows'}\n"
                f"• Debt/Equity: {dte} — leverage risk in rising rate environment\n"
                f"• Revenue growth: {rev_g} — may decelerate as market matures\n"
                f"• Competitive and macro headwinds remain a risk for {ticker}"
            )

        state["bear_thesis"] = bear_thesis
        logger.info("BearAgent: thesis generated for %s", ticker)
        return state
