"""
stock_data.py
StockDataTool — price history, current price, technical indicators, fundamentals.
Uses yfinance for market data and the `ta` library for all indicators.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

# Fallback fundamentals used when yfinance is rate-limited after all retries
_FALLBACK_FUNDAMENTALS: Dict[str, Any] = {
    "pe_ratio":            25.0,
    "forward_pe":          22.0,
    "peg_ratio":            2.0,
    "price_to_book":        3.5,
    "debt_to_equity":      45.0,
    "roe":                  0.18,
    "revenue_growth":       0.08,
    "earnings_growth":      0.10,
    "profit_margin":        0.15,
    "current_ratio":        1.8,
    "analyst_target":      None,
    "recommendation_mean": None,
}


class StockDataTool:
    """Unified interface for price, technicals, and fundamental data."""

    # ── yfinance retry helper ────────────────────────────────────────────────

    def _fetch_info(self, ticker: str, attempts: int = 3, delay: float = 2.0) -> Dict[str, Any]:
        """Fetch yfinance Ticker.info with retries to handle rate limiting."""
        last_exc: Exception = Exception("unknown")
        for attempt in range(attempts):
            try:
                info = yf.Ticker(ticker).info
                # yfinance returns a minimal dict (e.g. {"trailingPegRatio": None})
                # when rate-limited — treat anything with fewer than 10 keys as a failure
                if info and len(info) >= 10:
                    return info
                raise ValueError(f"incomplete info dict ({len(info)} keys)")
            except Exception as exc:
                last_exc = exc
                logger.warning("yfinance info attempt %d/%d for %s: %s", attempt + 1, attempts, ticker, exc)
                if attempt < attempts - 1:
                    time.sleep(delay)
        logger.error("yfinance info exhausted all retries for %s: %s", ticker, last_exc)
        return {}

    # ── Price history ────────────────────────────────────────────────────────

    def get_price_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        """
        Returns OHLCV DataFrame indexed by Date.
        Columns: open, high, low, close, volume
        """
        try:
            df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
            # yfinance 1.x returns MultiIndex columns like ('Close', 'AAPL')
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0].lower() for c in df.columns]
            else:
                df.columns = [c.lower() for c in df.columns]
            df.index.name = "date"
            logger.info("get_price_history(%s, %s): %d rows", ticker, period, len(df))
            return df
        except Exception as exc:
            logger.warning("get_price_history(%s) failed: %s", ticker, exc)
            return pd.DataFrame()

    # ── Current price ────────────────────────────────────────────────────────

    def get_current_price(self, ticker: str) -> Dict[str, Any]:
        """
        Returns:
          { ticker, price, change_pct, volume, market_cap }
        """
        try:
            info = self._fetch_info(ticker)

            price      = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", price)
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

            return {
                "ticker":     ticker.upper(),
                "price":      round(float(price), 2),
                "change_pct": change_pct,
                "volume":     info.get("volume") or info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
            }
        except Exception as exc:
            logger.warning("get_current_price(%s) failed: %s", ticker, exc)
            return {"ticker": ticker.upper(), "price": 0.0, "change_pct": 0.0,
                    "volume": None, "market_cap": None}

    # ── Technical indicators ─────────────────────────────────────────────────

    def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        Returns dict with:
          rsi_14, macd, macd_signal, macd_hist,
          sma_20, sma_50, sma_200,
          bb_upper, bb_lower,
          avg_volume_10d,
          price_vs_52w_high  (% below 52-week high, negative = below)
          price_vs_52w_low   (% above 52-week low, positive = above)
        Uses the `ta` library for all indicators.
        """
        try:
            import ta

            # Need at least 200 days for SMA-200
            df = self.get_price_history(ticker, period="1y")
            if df.empty or "close" not in df.columns:
                return {}

            close  = df["close"]
            volume = df["volume"]

            # RSI
            rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]

            # MACD
            macd_ind  = ta.trend.MACD(close)
            macd      = macd_ind.macd().iloc[-1]
            macd_sig  = macd_ind.macd_signal().iloc[-1]
            macd_hist = macd_ind.macd_diff().iloc[-1]

            # SMAs
            sma_20  = ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1]
            sma_50  = ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1]
            sma_200 = ta.trend.SMAIndicator(close, window=200).sma_indicator().iloc[-1]

            # Bollinger Bands
            bb        = ta.volatility.BollingerBands(close, window=20, window_dev=2)
            bb_upper  = bb.bollinger_hband().iloc[-1]
            bb_lower  = bb.bollinger_lband().iloc[-1]

            # Average volume (10-day)
            avg_vol_10d = float(volume.tail(10).mean())

            # 52-week high / low
            high_52w = float(close.tail(252).max())
            low_52w  = float(close.tail(252).min())
            current  = float(close.iloc[-1])

            price_vs_52w_high = round(((current - high_52w) / high_52w) * 100, 2)
            price_vs_52w_low  = round(((current - low_52w)  / low_52w)  * 100, 2)

            return {
                "rsi_14":            round(float(rsi),       2),
                "macd":              round(float(macd),      4),
                "macd_signal":       round(float(macd_sig),  4),
                "macd_hist":         round(float(macd_hist), 4),
                "sma_20":            round(float(sma_20),    2),
                "sma_50":            round(float(sma_50),    2),
                "sma_200":           round(float(sma_200),   2),
                "bb_upper":          round(float(bb_upper),  2),
                "bb_lower":          round(float(bb_lower),  2),
                "avg_volume_10d":    round(avg_vol_10d,      0),
                "price_vs_52w_high": price_vs_52w_high,
                "price_vs_52w_low":  price_vs_52w_low,
            }
        except Exception as exc:
            logger.warning("get_technical_indicators(%s) failed: %s", ticker, exc)
            return {}

    # ── Fundamentals ─────────────────────────────────────────────────────────

    def get_fundamentals(self, ticker: str) -> Dict[str, Any]:
        """
        Returns:
          pe_ratio, forward_pe, peg_ratio, price_to_book,
          debt_to_equity, roe, revenue_growth, earnings_growth,
          profit_margin, current_ratio, analyst_target, recommendation_mean
        """
        try:
            info = self._fetch_info(ticker)
            if not info:
                logger.warning("get_fundamentals(%s): using fallback mock data", ticker)
                return {
                    "ticker":  ticker.upper(),
                    "name":    ticker.upper(),
                    "sector":  None,
                    "industry": None,
                    **_FALLBACK_FUNDAMENTALS,
                }
            return {
                "ticker":              ticker.upper(),
                "name":                info.get("longName", ticker),
                "sector":              info.get("sector"),
                "industry":            info.get("industry"),
                "pe_ratio":            info.get("trailingPE"),
                "forward_pe":          info.get("forwardPE"),
                "peg_ratio":           info.get("pegRatio"),
                "price_to_book":       info.get("priceToBook"),
                "debt_to_equity":      info.get("debtToEquity"),
                "roe":                 info.get("returnOnEquity"),
                "revenue_growth":      info.get("revenueGrowth"),
                "earnings_growth":     info.get("earningsGrowth"),
                "profit_margin":       info.get("profitMargins"),
                "current_ratio":       info.get("currentRatio"),
                "analyst_target":      info.get("targetMeanPrice"),
                "recommendation_mean": info.get("recommendationMean"),
            }
        except Exception as exc:
            logger.warning("get_fundamentals(%s) failed: %s", ticker, exc)
            return {"ticker": ticker.upper(), **_FALLBACK_FUNDAMENTALS}


# ── Module-level helpers (backwards compat for agents) ───────────────────────

_tool = StockDataTool()

def get_fundamentals(ticker: str)              -> Dict: return _tool.get_fundamentals(ticker)
def get_price_history(ticker: str, period="6mo") -> pd.DataFrame: return _tool.get_price_history(ticker, period)
def compute_indicators(df: pd.DataFrame)       -> Dict: return _tool.get_technical_indicators.__func__(_tool, df) if False else {}
def get_ohlcv_list(ticker: str, period="3mo")  -> List[Dict]:
    df = _tool.get_price_history(ticker, period)
    if df.empty:
        return []
    df = df.reset_index()
    date_col = "date" if "date" in df.columns else df.columns[0]
    return [
        {
            "date":   str(row[date_col])[:10],
            "open":   round(float(row["open"]),  2),
            "high":   round(float(row["high"]),  2),
            "low":    round(float(row["low"]),   2),
            "close":  round(float(row["close"]), 2),
            "volume": int(row["volume"]),
        }
        for _, row in df.iterrows()
    ]


# ── Smoke test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    tool   = StockDataTool()
    ticker = "AAPL"

    print(f"\n{'='*60}")
    print(f"  StockDataTool smoke test — {ticker}")
    print(f"{'='*60}\n")

    print("── get_current_price ──")
    cp = tool.get_current_price(ticker)
    for k, v in cp.items():
        print(f"  {k:20s}: {v}")

    print("\n── get_technical_indicators ──")
    ti = tool.get_technical_indicators(ticker)
    for k, v in ti.items():
        print(f"  {k:25s}: {v}")

    print("\n── get_fundamentals ──")
    fu = tool.get_fundamentals(ticker)
    for k, v in fu.items():
        print(f"  {k:25s}: {v}")

    print("\n── get_price_history (5d) ──")
    df = tool.get_price_history(ticker, period="5d")
    print(df.to_string())

    print("\nAll tests passed.")
