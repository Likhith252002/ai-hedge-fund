"""
news_fetcher.py
NewsFetcher — news headlines from yfinance, Yahoo Finance search API,
Alpha Vantage, and BeautifulSoup scraper (cascading fallbacks).
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, List

import requests

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

_POS_WORDS = {
    "surge", "soar", "beat", "profit", "growth", "record", "gain", "rally",
    "strong", "upgrade", "bullish", "outperform", "exceed", "positive",
    "revenue", "expand", "innovation", "breakthrough", "dividend", "buy",
    "rise", "high", "jump", "boost", "success", "win", "confident", "robust",
}
_NEG_WORDS = {
    "fall", "drop", "miss", "loss", "decline", "layoff", "cut", "downgrade",
    "bearish", "underperform", "negative", "weak", "debt", "lawsuit", "fine",
    "recall", "fraud", "crash", "sell", "low", "plunge", "risk", "concern",
    "warn", "struggle", "disappoint", "deficit", "volatile", "fear",
}


class NewsFetcher:
    """Aggregates news from multiple sources with cascading fallbacks."""

    def get_news(self, ticker: str, company_name: str = "") -> List[Dict[str, Any]]:
        """
        Returns up to 10 recent articles. Sources tried in order:
          1. yfinance .news
          2. Yahoo Finance search API (JSON)
          3. Alpha Vantage NEWS_SENTIMENT (demo key)
          4. BeautifulSoup scrape of Yahoo Finance RSS
        Guarantees at least 3 articles if any source succeeds.
        """
        articles: List[Dict] = []

        # Source 1: yfinance
        articles.extend(self._fetch_yfinance_news(ticker))
        logger.info("After yfinance: %d articles for %s", len(articles), ticker)

        # Source 2: Yahoo Finance search JSON (fast and reliable)
        if len(articles) < 3:
            articles.extend(self._fetch_yahoo_search(ticker))
            logger.info("After Yahoo search: %d articles for %s", len(articles), ticker)

        # Source 3: Alpha Vantage
        if len(articles) < 3:
            try:
                articles.extend(self._fetch_alphavantage_news(ticker))
                logger.info("After Alpha Vantage: %d articles for %s", len(articles), ticker)
            except Exception as exc:
                logger.warning("Alpha Vantage news failed: %s", exc)

        # Source 4: Yahoo Finance RSS scraper (last resort)
        if len(articles) < 3:
            articles.extend(self._fetch_yahoo_rss(ticker))
            logger.info("After RSS scraper: %d articles for %s", len(articles), ticker)

        # Deduplicate, sort, cap
        seen:   set  = set()
        unique: List = []
        for a in articles:
            key = a.get("title", "").strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(a)

        unique.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        result = unique[:10]
        logger.info("get_news(%s): returning %d articles", ticker, len(result))
        return result

    # ── Source 1: yfinance ───────────────────────────────────────────────────

    def _fetch_yfinance_news(self, ticker: str) -> List[Dict]:
        try:
            import yfinance as yf
            session = requests.Session()
            session.headers.update({"User-Agent": _UA})
            raw = yf.Ticker(ticker, session=session).news or []
            articles = []
            for item in raw:
                content   = item.get("content", item)
                provider  = content.get("provider", {})
                canon_url = content.get("canonicalUrl", {}).get("url", item.get("link", ""))
                title     = content.get("title", item.get("title", ""))
                summary   = content.get("summary", content.get("description", ""))
                published = content.get("pubDate", "")
                if not title:
                    continue
                articles.append({
                    "title":           title,
                    "summary":         _strip_html(summary)[:300],
                    "source":          provider.get("displayName", "Yahoo Finance"),
                    "published_at":    published,
                    "sentiment_score": self.analyze_sentiment(title + " " + summary),
                    "url":             canon_url,
                })
            logger.info("yfinance news(%s): %d articles", ticker, len(articles))
            return articles
        except Exception as exc:
            logger.warning("_fetch_yfinance_news(%s) failed: %s", ticker, exc)
            return []

    # ── Source 2: Yahoo Finance search API ───────────────────────────────────

    def _fetch_yahoo_search(self, ticker: str) -> List[Dict]:
        """Yahoo Finance v1 search endpoint — returns news JSON without auth."""
        try:
            url  = "https://query1.finance.yahoo.com/v1/finance/search"
            resp = requests.get(
                url,
                headers={"User-Agent": _UA},
                params={
                    "q":                ticker,
                    "newsCount":        8,
                    "enableFuzzyQuery": "false",
                    "lang":             "en-US",
                },
                timeout=10,
            )
            resp.raise_for_status()
            news_items = resp.json().get("news", [])
            articles   = []
            for item in news_items:
                title = item.get("title", "")
                if not title:
                    continue
                pub_ts = item.get("providerPublishTime")
                pub_str = (
                    datetime.utcfromtimestamp(pub_ts).isoformat() if pub_ts else ""
                )
                articles.append({
                    "title":           title,
                    "summary":         "",
                    "source":          item.get("publisher", "Yahoo Finance"),
                    "published_at":    pub_str,
                    "sentiment_score": self.analyze_sentiment(title),
                    "url":             item.get("link", ""),
                })
            logger.info("_fetch_yahoo_search(%s): %d articles", ticker, len(articles))
            return articles
        except Exception as exc:
            logger.warning("_fetch_yahoo_search(%s) failed: %s", ticker, exc)
            return []

    # ── Source 3: Alpha Vantage ──────────────────────────────────────────────

    def _fetch_alphavantage_news(self, ticker: str) -> List[Dict]:
        url  = (
            "https://www.alphavantage.co/query"
            f"?function=NEWS_SENTIMENT&tickers={ticker}&limit=5&apikey=demo"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        feed     = resp.json().get("feed", [])
        articles = []
        for item in feed[:5]:
            sentiment_score = 0.0
            for ts in item.get("ticker_sentiment", []):
                if ts.get("ticker", "").upper() == ticker.upper():
                    sentiment_score = float(ts.get("ticker_sentiment_score", 0))
                    break
            articles.append({
                "title":           item.get("title", ""),
                "summary":         item.get("summary", "")[:300],
                "source":          item.get("source", "Alpha Vantage"),
                "published_at":    item.get("time_published", ""),
                "sentiment_score": round(sentiment_score, 3),
                "url":             item.get("url", ""),
            })
        logger.info("Alpha Vantage news(%s): %d articles", ticker, len(articles))
        return articles

    # ── Source 4: Yahoo Finance RSS ──────────────────────────────────────────

    def _fetch_yahoo_rss(self, ticker: str) -> List[Dict]:
        """Parse Yahoo Finance RSS feed using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup
            url  = (
                f"https://feeds.finance.yahoo.com/rss/2.0/headline"
                f"?s={ticker}&region=US&lang=en-US"
            )
            resp = requests.get(url, headers={"User-Agent": _UA}, timeout=10)
            resp.raise_for_status()
            soup     = BeautifulSoup(resp.text, "html.parser")
            items    = soup.find_all("item")
            articles = []
            for item in items[:5]:
                title_tag = item.find("title")
                desc_tag  = item.find("description")
                pub_tag   = item.find("pubdate")
                link_tag  = item.find("link")
                title = title_tag.get_text(strip=True) if title_tag else ""
                if not title or title.lower() == ticker.lower():
                    continue
                desc    = _strip_html(desc_tag.get_text(strip=True) if desc_tag else "")
                pub_str = pub_tag.get_text(strip=True) if pub_tag else ""
                link    = link_tag.get_text(strip=True) if link_tag else ""
                articles.append({
                    "title":           title,
                    "summary":         desc[:300],
                    "source":          "Yahoo Finance",
                    "published_at":    pub_str,
                    "sentiment_score": self.analyze_sentiment(title),
                    "url":             link,
                })
            logger.info("_fetch_yahoo_rss(%s): %d articles", ticker, len(articles))
            return articles
        except Exception as exc:
            logger.warning("_fetch_yahoo_rss(%s) failed: %s", ticker, exc)
            return []

    # ── Reddit sentiment ─────────────────────────────────────────────────────

    def get_reddit_sentiment(self, ticker: str) -> Dict[str, Any]:
        url     = f"https://www.reddit.com/search.json?q={ticker}+stock&sort=new&limit=25"
        headers = {"User-Agent": "ai-hedge-fund/1.0"}
        try:
            resp   = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            posts  = resp.json().get("data", {}).get("children", [])
            titles = [p["data"]["title"] for p in posts if p.get("data", {}).get("title")]
            scores = [self.analyze_sentiment(t) for t in titles]
            avg    = round(sum(scores) / len(scores), 3) if scores else 0.0
            return {"mention_count": len(titles), "avg_sentiment": avg, "top_posts": titles[:5]}
        except Exception as exc:
            logger.warning("get_reddit_sentiment(%s) failed: %s", ticker, exc)
            return {"mention_count": 0, "avg_sentiment": 0.0, "top_posts": []}

    # ── Sentiment analysis ───────────────────────────────────────────────────

    def analyze_sentiment(self, text: str) -> float:
        if not text:
            return 0.0
        words = set(re.findall(r"\b\w+\b", text.lower()))
        pos   = len(words & _POS_WORDS)
        neg   = len(words & _NEG_WORDS)
        total = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 3)


# ── Module-level helper ───────────────────────────────────────────────────────

_fetcher = NewsFetcher()

def get_news(ticker: str, limit: int = 10) -> List[Dict]:
    return _fetcher.get_news(ticker)[:limit]


# ── HTML stripping ────────────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()
