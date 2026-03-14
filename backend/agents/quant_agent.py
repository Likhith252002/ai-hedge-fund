"""
quant_agent.py
Computes technical indicators and quantitative signals for a ticker.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


class QuantAgent:
    """
    Computes technical signals:
    - RSI, MACD, Bollinger Bands, SMA crossovers
    - Momentum, volatility, and mean-reversion scores
    - Outputs a quant_signal: "BUY" | "SELL" | "NEUTRAL"
    """

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("QuantAgent: computing signals for %s", ticker)

        from tools.stock_data import StockDataTool

        tool       = StockDataTool()
        indicators = tool.get_technical_indicators(ticker)

        # Correct key names: rsi_14, macd, sma_20, sma_50 from StockDataTool
        rsi    = indicators.get("rsi_14", 50)
        macd   = indicators.get("macd", 0)
        sma_20 = indicators.get("sma_20", 0)
        sma_50 = indicators.get("sma_50", 0)

        # Signal logic: RSI + MACD + SMA crossover
        buy_signals  = 0
        sell_signals = 0

        if rsi < 35:
            buy_signals += 1
        elif rsi > 65:
            sell_signals += 1

        if macd > 0:
            buy_signals += 1
        elif macd < 0:
            sell_signals += 1

        if sma_20 > sma_50:          # golden cross
            buy_signals += 1
        elif sma_20 < sma_50:        # death cross
            sell_signals += 1

        if buy_signals >= 2:
            signal = "BUY"
        elif sell_signals >= 2:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        state["indicators"]   = indicators
        state["quant_signal"] = signal
        logger.info(
            "QuantAgent: signal=%s  RSI=%.1f  MACD=%.4f  SMA20=%.2f  SMA50=%.2f",
            signal, rsi, macd, sma_20, sma_50,
        )
        return state
