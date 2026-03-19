"""
test_sentiment.py
Unit tests for NewsFetcher.analyze_sentiment().
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.news_fetcher import NewsFetcher

_f = NewsFetcher()


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_string_returns_zero():
    assert _f.analyze_sentiment("") == 0.0


def test_neutral_text_returns_zero():
    assert _f.analyze_sentiment("The company released a quarterly report today") == 0.0


def test_whitespace_only_returns_zero():
    assert _f.analyze_sentiment("   ") == 0.0


# ── Positive headlines ────────────────────────────────────────────────────────

@pytest.mark.parametrize("headline", [
    "Apple beats earnings estimates, reports record revenue",
    "NVDA surges on strong quarterly profit, analysts upgrade to buy",
    "Amazon launches new AI chip, dividend increase announced",
])
def test_positive_headlines_score_positive(headline):
    score = _f.analyze_sentiment(headline)
    assert score > 0, f"Expected positive score for: '{headline}', got {score}"


# ── Negative headlines ────────────────────────────────────────────────────────

@pytest.mark.parametrize("headline", [
    "Tesla misses earnings expectations, shares fall sharply",
    "Meta cuts thousands of jobs in massive layoffs, shares plunge",
    "Company faces fraud investigation, analysts downgrade to sell",
])
def test_negative_headlines_score_negative(headline):
    score = _f.analyze_sentiment(headline)
    assert score < 0, f"Expected negative score for: '{headline}', got {score}"


# ── Score bounds ──────────────────────────────────────────────────────────────

def test_score_within_bounds():
    for text in [
        "surge beat record profit buy bullish strong",
        "crash fall loss fraud sell bearish weak",
        "The company announced results for the fiscal quarter",
    ]:
        score = _f.analyze_sentiment(text)
        assert -1.0 <= score <= 1.0, f"Score out of [-1, 1]: {score} for '{text}'"


# ── Database ──────────────────────────────────────────────────────────────────

def test_db_init_and_metrics(tmp_path, monkeypatch):
    """init_db() creates the schema; get_metrics() returns the right shape."""
    monkeypatch.setenv("DB_PATH_OVERRIDE", str(tmp_path / "test.db"))

    import importlib
    import db.database as dbmod

    # Patch the internal path
    dbmod._DB_PATH = tmp_path / "test.db"
    dbmod.init_db()

    m = dbmod.get_metrics()
    assert m["total_analyses"] == 0
    assert m["popular_stocks"] == []
    assert m["decision_distribution"] == {}


def test_db_save_and_retrieve(tmp_path, monkeypatch):
    import db.database as dbmod

    dbmod._DB_PATH = tmp_path / "test2.db"
    dbmod.init_db()

    fake_result = {
        "ticker": "AAPL",
        "decision": {"action": "BUY", "confidence": 72, "position_size": 5.0, "rationale": "test"},
        "quant_signal": "BUY",
    }
    row_id = dbmod.save_analysis("AAPL", fake_result, execution_time_ms=12000)
    assert isinstance(row_id, int) and row_id > 0

    item = dbmod.get_analysis_by_id(row_id)
    assert item is not None
    assert item["ticker"] == "AAPL"
    assert item["action"] == "BUY"
    assert item["confidence"] == 72

    recent = dbmod.get_recent_analyses(limit=5)
    assert len(recent) == 1
    assert recent[0]["ticker"] == "AAPL"

    m = dbmod.get_metrics()
    assert m["total_analyses"] == 1
    assert m["decision_distribution"].get("BUY") == 1
