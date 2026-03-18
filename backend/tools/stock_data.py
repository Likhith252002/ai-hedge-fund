"""
stock_data.py
StockDataTool — price history, current price, technical indicators, fundamentals.
Uses yfinance with session-based retry + Yahoo Finance v8 backup.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import requests
import yfinance as yf

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Fallback fundamentals when yfinance is rate-limited after all retries
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

    # ── Session helper ───────────────────────────────────────────────────────

    def _get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": _UA})
        return session

    # ── History (primary internal method) ────────────────────────────────────

    def _fetch_history(
        self, ticker: str, period: str = "3mo",
        attempts: int = 3, delay: float = 2.0,
    ) -> pd.DataFrame:
        """Fetch OHLCV via yf.Ticker().history() with UA session + retries."""
        last_exc: Exception = Exception("unknown")
        for attempt in range(attempts):
            try:
                session = self._get_session()
                df = yf.Ticker(ticker, session=session).history(
                    period=period, auto_adjust=True
                )
                if not df.empty:
                    df.columns = [c.lower() for c in df.columns]
                    df.index.name = "date"
                    logger.info("_fetch_history(%s, %s): %d rows", ticker, period, len(df))
                    return df
                raise ValueError("empty DataFrame")
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "_fetch_history attempt %d/%d for %s: %s", attempt + 1, attempts, ticker, exc
                )
                if attempt < attempts - 1:
                    time.sleep(delay)
        logger.error("_fetch_history exhausted retries for %s: %s", ticker, last_exc)
        return pd.DataFrame()

    # ── yfinance info (with retry) ───────────────────────────────────────────

    def _fetch_info(self, ticker: str, attempts: int = 3, delay: float = 2.0) -> Dict[str, Any]:
        """Fetch yfinance Ticker.info with UA session + retries."""
        last_exc: Exception = Exception("unknown")
        for attempt in range(attempts):
            try:
                session = self._get_session()
                info = yf.Ticker(ticker, session=session).info
                if info and len(info) >= 10:
                    return info
                raise ValueError(f"incomplete info dict ({len(info)} keys)")
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "_fetch_info attempt %d/%d for %s: %s", attempt + 1, attempts, ticker, exc
                )
                if attempt < attempts - 1:
                    time.sleep(delay)
        logger.error("_fetch_info exhausted retries for %s: %s", ticker, last_exc)
        return {}

    # ── Price history ────────────────────────────────────────────────────────

    def get_price_history(self, ticker: str, period: str = "3mo") -> pd.DataFrame:
        """Returns OHLCV DataFrame indexed by Date (lowercase columns)."""
        return self._fetch_history(ticker, period)

    # ── Current price ────────────────────────────────────────────────────────

    def get_current_price(self, ticker: str) -> Dict[str, Any]:
        """Returns { ticker, price, change_pct, volume, market_cap }."""
        # Primary: yfinance info
        try:
            info = self._fetch_info(ticker)
            if info:
                price      = info.get("currentPrice") or info.get("regularMarketPrice") or 0
                prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
                change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0
                if price:
                    return {
                        "ticker":     ticker.upper(),
                        "price":      round(float(price), 2),
                        "change_pct": change_pct,
                        "volume":     info.get("volume") or info.get("regularMarketVolume"),
                        "market_cap": info.get("marketCap"),
                    }
        except Exception as exc:
            logger.warning("get_current_price yfinance failed for %s: %s", ticker, exc)

        # Backup: Yahoo Finance v8 chart API
        return self._fetch_price_v8(ticker)

    def _fetch_price_v8(self, ticker: str) -> Dict[str, Any]:
        """Fallback price via Yahoo Finance v8 chart API."""
        try:
            url  = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
            resp = requests.get(
                url, headers={"User-Agent": _UA}, timeout=10,
                params={"interval": "1d", "range": "5d"},
            )
            resp.raise_for_status()
            meta  = resp.json()["chart"]["result"][0]["meta"]
            price = float(meta.get("regularMarketPrice", 0))
            prev  = float(meta.get("chartPreviousClose") or meta.get("previousClose") or price)
            chg   = round(((price - prev) / prev) * 100, 2) if prev else 0.0
            logger.info("_fetch_price_v8(%s): price=%.2f", ticker, price)
            return {
                "ticker":     ticker.upper(),
                "price":      round(price, 2),
                "change_pct": chg,
                "volume":     meta.get("regularMarketVolume"),
                "market_cap": None,
            }
        except Exception as exc:
            logger.error("_fetch_price_v8(%s) failed: %s", ticker, exc)
            return {
                "ticker": ticker.upper(), "price": 0.0,
                "change_pct": 0.0, "volume": None, "market_cap": None,
            }

    # ── Technical indicators ─────────────────────────────────────────────────

    def get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """Returns RSI, MACD, SMA, Bollinger, 52w range. Falls back to manual RSI."""
        try:
            df = self._fetch_history(ticker, period="1y")
            if df.empty or "close" not in df.columns:
                logger.warning("get_technical_indicators(%s): empty history", ticker)
                return {}

            close  = df["close"]
            volume = df["volume"]

            # Try ta library first
            try:
                import ta
                rsi       = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
                macd_ind  = ta.trend.MACD(close)
                macd      = macd_ind.macd().iloc[-1]
                macd_sig  = macd_ind.macd_signal().iloc[-1]
                macd_hist = macd_ind.macd_diff().iloc[-1]
                sma_20    = ta.trend.SMAIndicator(close, window=20).sma_indicator().iloc[-1]
                sma_50    = ta.trend.SMAIndicator(close, window=50).sma_indicator().iloc[-1]
                sma_200   = ta.trend.SMAIndicator(close, window=200).sma_indicator().iloc[-1]
                bb        = ta.volatility.BollingerBands(close, window=20, window_dev=2)
                bb_upper  = bb.bollinger_hband().iloc[-1]
                bb_lower  = bb.bollinger_lband().iloc[-1]
            except Exception as ta_exc:
                logger.warning("ta library failed for %s, using manual calc: %s", ticker, ta_exc)
                rsi       = self._rsi_manual(close)
                macd, macd_sig, macd_hist = self._macd_manual(close)
                sma_20    = float(close.tail(20).mean())
                sma_50    = float(close.tail(50).mean())
                sma_200   = float(close.tail(200).mean()) if len(close) >= 200 else sma_50
                bb_mid    = sma_20
                bb_std    = float(close.tail(20).std())
                bb_upper  = bb_mid + 2 * bb_std
                bb_lower  = bb_mid - 2 * bb_std

            avg_vol_10d      = float(volume.tail(10).mean())
            high_52w         = float(close.tail(252).max())
            low_52w          = float(close.tail(252).min())
            current          = float(close.iloc[-1])
            price_vs_52w_high = round(((current - high_52w) / high_52w) * 100, 2)
            price_vs_52w_low  = round(((current - low_52w) / low_52w) * 100, 2)

            return {
                "rsi_14":             round(float(rsi),       2),
                "macd":               round(float(macd),      4),
                "macd_signal":        round(float(macd_sig),  4),
                "macd_hist":          round(float(macd_hist), 4),
                "sma_20":             round(float(sma_20),    2),
                "sma_50":             round(float(sma_50),    2),
                "sma_200":            round(float(sma_200),   2),
                "bb_upper":           round(float(bb_upper),  2),
                "bb_lower":           round(float(bb_lower),  2),
                "avg_volume_10d":     round(avg_vol_10d,      0),
                "price_vs_52w_high":  price_vs_52w_high,
                "price_vs_52w_low":   price_vs_52w_low,
            }
        except Exception as exc:
            logger.warning("get_technical_indicators(%s) failed: %s", ticker, exc)
            return {}

    def _rsi_manual(self, close: pd.Series, window: int = 14) -> float:
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(window).mean()
        loss  = -delta.clip(upper=0).rolling(window).mean()
        rs    = gain / loss
        rsi   = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])

    def _macd_manual(self, close: pd.Series):
        ema12     = close.ewm(span=12, adjust=False).mean()
        ema26     = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal    = macd_line.ewm(span=9, adjust=False).mean()
        hist      = macd_line - signal
        return float(macd_line.iloc[-1]), float(signal.iloc[-1]), float(hist.iloc[-1])

    # ── Fundamentals ─────────────────────────────────────────────────────────

    def get_fundamentals(self, ticker: str) -> Dict[str, Any]:
        """Returns 12+ fundamental metrics. Falls back to market-average mock data."""
        try:
            info = self._fetch_info(ticker)
            if not info:
                logger.warning("get_fundamentals(%s): using fallback mock data", ticker)
                return {"ticker": ticker.upper(), "name": ticker.upper(),
                        "sector": None, "industry": None, **_FALLBACK_FUNDAMENTALS}
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

def get_fundamentals(ticker: str)               -> Dict:  return _tool.get_fundamentals(ticker)
def get_price_history(ticker: str, period="6mo") -> pd.DataFrame: return _tool.get_price_history(ticker, period)
def get_ohlcv_list(ticker: str, period="3mo")   -> List[Dict]:
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
