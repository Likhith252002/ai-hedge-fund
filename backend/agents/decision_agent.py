"""
decision_agent.py
Synthesises bull + bear theses and quant signals into a final
investment decision with confidence score and position sizing.
Calls the Anthropic API directly — no LangChain wrapper, no fallback.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import anthropic

logger = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"

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

Even with limited data, you MUST make a definitive investment recommendation.
Uncertainty is not an excuse for inaction. A real portfolio manager always decides.

Weigh the bull and bear theses against the quantitative signals and fundamentals.
Make a concrete, specific BUY, SELL, or HOLD call with a real confidence percentage
between 30 and 90. Confidence reflects how strongly the evidence points in one direction.

Respond in exactly this format — no extra text, no explanation outside these lines:
DECISION: <BUY|SELL|HOLD>
CONFIDENCE: <integer between 30 and 90>
POSITION_SIZE: <decimal between 0.0 and 10.0>
RATIONALE: <one specific sentence referencing the actual data above>
"""


class DecisionAgent:
    def __init__(self, llm=None):
        pass  # llm param kept for API compatibility but ignored

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("DecisionAgent: synthesising decision for %s", ticker)

        ind  = state.get("indicators", {})
        fund = state.get("fundamentals", {})

        from tools.stock_data import StockDataTool
        price_data    = StockDataTool().get_current_price(ticker)
        current_price = price_data.get("price", 0)

        def _pct(v):
            return f"{v*100:.1f}%" if v is not None else "N/A"

        sma_20    = ind.get("sma_20", 0) or 0
        sma_50    = ind.get("sma_50", 0) or 0
        sma_cross = f"{sma_20:.2f} {'>' if sma_20 > sma_50 else '<'} {sma_50:.2f}"

        prompt = DECISION_PROMPT.format(
            ticker            = ticker,
            current_price     = current_price,
            rsi_14            = ind.get("rsi_14", "N/A"),
            macd              = ind.get("macd", "N/A"),
            sma_cross         = sma_cross,
            price_vs_52w_high = ind.get("price_vs_52w_high", "N/A"),
            pe_ratio          = fund.get("pe_ratio", "N/A"),
            forward_pe        = fund.get("forward_pe", "N/A"),
            roe               = _pct(fund.get("roe")),
            revenue_growth    = _pct(fund.get("revenue_growth")),
            analyst_target    = fund.get("analyst_target", "N/A"),
            bull_thesis       = state.get("bull_thesis", "No bull thesis available."),
            bear_thesis       = state.get("bear_thesis", "No bear thesis available."),
            quant_signal      = state.get("quant_signal", "NEUTRAL"),
        )

        client  = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = await client.messages.create(
            model=_MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text
        logger.info("DecisionAgent raw response for %s:\n%s", ticker, raw)

        decision = _parse_decision(raw)
        decision["current_price"] = current_price

        state["decision"] = decision
        logger.info(
            "DecisionAgent: %s — action=%s confidence=%s%%",
            ticker, decision["action"], decision["confidence"],
        )
        return state


def _parse_decision(raw: str) -> Dict[str, Any]:
    lines: Dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            lines[key.strip().upper()] = val.strip()

    action = lines.get("DECISION", "HOLD").upper()
    if action not in ("BUY", "SELL", "HOLD"):
        action = "HOLD"

    try:
        confidence = int(lines.get("CONFIDENCE", "55").replace("%", "").strip())
        confidence = max(30, min(90, confidence))   # clamp to [30, 90]
    except ValueError:
        confidence = 55

    try:
        position_size = float(lines.get("POSITION_SIZE", "3").replace("%", "").strip())
        position_size = max(0.0, min(10.0, position_size))
    except ValueError:
        position_size = 3.0

    rationale = lines.get("RATIONALE", "Decision based on available quantitative and qualitative signals.")

    return {
        "action":        action,
        "confidence":    confidence,
        "position_size": position_size,
        "rationale":     rationale,
    }
