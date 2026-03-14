"""
research_agent.py
Fetches fundamental data, news, and SEC filings for a given ticker.
Summarises findings for downstream agents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ResearchAgent:
    """
    Gathers raw market intelligence:
    - Company fundamentals via yfinance
    - Recent news headlines via NewsFetcher
    - Key financial ratios (P/E, EPS, revenue growth)
    """

    def __init__(self, news_fetcher=None):
        self.news_fetcher = news_fetcher

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        ticker = state["ticker"]
        logger.info("ResearchAgent: analysing %s", ticker)

        from tools.stock_data import StockDataTool
        from tools.news_fetcher import NewsFetcher

        fundamentals = StockDataTool().get_fundamentals(ticker)
        news         = NewsFetcher().get_news(ticker, company_name=fundamentals.get("name", ""))

        state["fundamentals"] = fundamentals
        state["news"]         = news

        # Build a richer research summary using correct field names from StockDataTool
        pe      = fundamentals.get("pe_ratio", "N/A")
        fwd_pe  = fundamentals.get("forward_pe", "N/A")
        pb      = fundamentals.get("price_to_book", "N/A")
        roe     = fundamentals.get("roe")
        rev_g   = fundamentals.get("revenue_growth")
        margin  = fundamentals.get("profit_margin")
        rec     = fundamentals.get("recommendation_mean", "N/A")
        name    = fundamentals.get("name", ticker)

        roe_str   = f"{roe*100:.1f}%"    if roe    is not None else "N/A"
        rev_g_str = f"{rev_g*100:.1f}%"  if rev_g  is not None else "N/A"
        margin_str= f"{margin*100:.1f}%" if margin  is not None else "N/A"

        avg_sentiment = (
            sum(n.get("sentiment_score", 0) for n in news) / len(news)
            if news else 0.0
        )

        state["research_summary"] = (
            f"{name} ({ticker}) — "
            f"P/E: {pe}, Forward P/E: {fwd_pe}, P/B: {pb} | "
            f"ROE: {roe_str}, Rev growth: {rev_g_str}, Profit margin: {margin_str} | "
            f"Analyst rec: {rec} | "
            f"News sentiment (avg): {avg_sentiment:+.2f} across {len(news)} articles"
        )
        logger.info("ResearchAgent: done — %s", state["research_summary"])
        return state
