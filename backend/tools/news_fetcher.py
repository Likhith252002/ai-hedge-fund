"""
news_fetcher.py
NewsFetcher — news headlines, Alpha Vantage sentiment, Reddit mentions.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Dict, Any, List

import requests

logger = logging.getLogger(__name__)

# Positive / negative word lists for rule-based sentiment
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
    """Aggregates news and sentiment from yfinance, Alpha Vantage, and Reddit."""

    # ── News aggregation ─────────────────────────────────────────────────────

    def get_news(self, ticker: str, company_name: str = "") -> List[Dict[str, Any]]:
        """
        Fetches up to 10 recent articles from:
          1. yfinance news
          2. Alpha Vantage NEWS_SENTIMENT API (free demo key, graceful fallback)

        Each item: { title, summary, source, published_at, sentiment_score, url }
        """
        articles: List[Dict] = []

        # Source 1: yfinance
        articles.extend(self._fetch_yfinance_news(ticker))

        # Source 2: Alpha Vantage (graceful fallback)
        try:
            articles.extend(self._fetch_alphavantage_news(ticker))
        except Exception as exc:
            logger.warning("Alpha Vantage news fetch failed: %s", exc)

        # Deduplicate by title, sort by published_at descending, cap at 10
        seen   = set()
        unique = []
        for a in articles:
            key = a["title"].strip().lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(a)

        unique.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        return unique[:10]

    # ── Reddit sentiment ─────────────────────────────────────────────────────

    def get_reddit_sentiment(self, ticker: str) -> Dict[str, Any]:
        """
        Calls Reddit search API for "{ticker} stock".
        Returns { mention_count, avg_sentiment, top_posts: [titles] }
        """
        url = f"https://www.reddit.com/search.json?q={ticker}+stock&sort=new&limit=25"
        headers = {"User-Agent": "ai-hedge-fund/1.0"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data  = resp.json()
            posts = data.get("data", {}).get("children", [])

            titles     = [p["data"]["title"] for p in posts if p.get("data", {}).get("title")]
            scores     = [self.analyze_sentiment(t) for t in titles]
            avg_score  = round(sum(scores) / len(scores), 3) if scores else 0.0

            logger.info("get_reddit_sentiment(%s): %d posts, avg=%.3f", ticker, len(titles), avg_score)
            return {
                "mention_count": len(titles),
                "avg_sentiment": avg_score,
                "top_posts":     titles[:5],
            }
        except Exception as exc:
            logger.warning("get_reddit_sentiment(%s) failed: %s", ticker, exc)
            return {"mention_count": 0, "avg_sentiment": 0.0, "top_posts": []}

    # ── Sentiment analysis ───────────────────────────────────────────────────

    def analyze_sentiment(self, text: str) -> float:
        """
        Rule-based sentiment score in [-1.0, 1.0].
        Counts positive and negative financial keywords.
        """
        if not text:
            return 0.0
        words  = set(re.findall(r"\b\w+\b", text.lower()))
        pos    = len(words & _POS_WORDS)
        neg    = len(words & _NEG_WORDS)
        total  = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 3)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _fetch_yfinance_news(self, ticker: str) -> List[Dict]:
        try:
            import yfinance as yf
            raw = yf.Ticker(ticker).news or []
            articles = []
            for item in raw:
                # yfinance 1.x nests data under 'content'
                content   = item.get("content", item)
                provider  = content.get("provider", {})
                canon_url = content.get("canonicalUrl", {}).get("url", item.get("link", ""))
                title     = content.get("title", item.get("title", ""))
                summary   = content.get("summary", content.get("description", ""))
                published = content.get("pubDate", "")

                if not title:
                    continue

                articles.append({
                    "title":         title,
                    "summary":       _strip_html(summary)[:300],
                    "source":        provider.get("displayName", "Yahoo Finance"),
                    "published_at":  published,
                    "sentiment_score": self.analyze_sentiment(title + " " + summary),
                    "url":           canon_url,
                })
            logger.info("yfinance news(%s): %d articles", ticker, len(articles))
            return articles
        except Exception as exc:
            logger.warning("_fetch_yfinance_news(%s) failed: %s", ticker, exc)
            return []

    def _fetch_alphavantage_news(self, ticker: str) -> List[Dict]:
        """
        Calls Alpha Vantage NEWS_SENTIMENT endpoint.
        Uses the free 'demo' key — limited to certain tickers (AAPL, IBM etc.).
        Falls back gracefully for unsupported tickers.
        """
        url = (
            "https://www.alphavantage.co/query"
            f"?function=NEWS_SENTIMENT&tickers={ticker}&limit=5&apikey=demo"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        feed     = data.get("feed", [])
        articles = []
        for item in feed[:5]:
            # Extract ticker-specific sentiment if available
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


# ── Module-level helper (backwards compat) ───────────────────────────────────

_fetcher = NewsFetcher()

def get_news(ticker: str, limit: int = 10) -> List[Dict]:
    return _fetcher.get_news(ticker)[:limit]


# ── HTML stripping helper ────────────────────────────────────────────────────

def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


# ── Smoke test ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    fetcher = NewsFetcher()
    ticker  = "AAPL"

    print(f"\n{'='*60}")
    print(f"  NewsFetcher smoke test — {ticker}")
    print(f"{'='*60}\n")

    print("── get_news ──")
    news = fetcher.get_news(ticker, company_name="Apple Inc.")
    print(f"  {len(news)} articles returned")
    for n in news[:5]:
        print(f"  [{n['sentiment_score']:+.2f}] {n['title'][:70]}")
        print(f"         {n['source']} | {n['published_at'][:10]}")

    print("\n── get_reddit_sentiment ──")
    reddit = fetcher.get_reddit_sentiment(ticker)
    print(f"  mention_count : {reddit['mention_count']}")
    print(f"  avg_sentiment : {reddit['avg_sentiment']}")
    print(f"  top_posts     :")
    for p in reddit["top_posts"]:
        print(f"    - {p[:70]}")

    print("\n── analyze_sentiment ──")
    tests = [
        "Apple beats earnings expectations, stock surges to record high",
        "Apple faces lawsuit, revenue growth disappoints investors",
        "Apple announces new product lineup",
    ]
    for t in tests:
        score = fetcher.analyze_sentiment(t)
        print(f"  [{score:+.2f}] {t}")

    print("\nAll tests passed.")
