"""
bear_agent.py
Constructs the bearish investment thesis using research + quant data.
Calls the Anthropic API directly. Returns clean prose — no markdown.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import anthropic

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

BEAR_PROMPT = """You are a skeptical equity analyst building a BEAR case for {ticker}.

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

Write 4 concise analytical paragraphs making the strongest possible bear case.
Cover key risks, valuation concerns, technical weakness signals, and negative macro factors.
Reference specific numbers from above. Be direct and specific.

IMPORTANT: Respond in plain prose paragraphs only. Do NOT use markdown headers (#),
bold (**), bullet points (-), horizontal rules (---), or any other markdown syntax.
Just write 4 clean paragraphs of analytical text separated by blank lines.
"""


class BearAgent:
    def __init__(self, llm=None):
        pass  # llm param kept for API compatibility but ignored

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("BearAgent: building bear thesis for %s", ticker)

        news_headlines = "\n".join(
            f"- {n['title']}" for n in state.get("news", [])[:5]
        ) or "No recent news available."

        ind  = state.get("indicators", {})
        fund = state.get("fundamentals", {})

        def _pct(v):
            return f"{v*100:.1f}%" if v is not None else "N/A"

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

        client  = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        bear_thesis = message.content[0].text

        state["bear_thesis"] = bear_thesis
        logger.info("BearAgent: thesis generated for %s", ticker)
        return state
