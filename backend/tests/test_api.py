"""
test_api.py
Tests for API endpoints: health, metrics, stock data, news, history, validation.
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.anyio


# ── Health ────────────────────────────────────────────────────────────────────

async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "ai-hedge-fund"


async def test_health_api_prefix(client):
    r = await client.get("/api/health")
    assert r.status_code == 200


# ── Ticker validation — REST endpoints ───────────────────────────────────────

@pytest.mark.parametrize("bad_ticker", [
    "TOOLONG",    # 6 chars
    "123",        # digits only
    "AA BB",      # space
    "",           # empty (path param, will 404 via FastAPI routing)
    "A!",         # special char
    "nvda",       # lowercase treated differently by our validator
])
async def test_stock_invalid_tickers(client, bad_ticker):
    if not bad_ticker:
        return  # empty path param routes to 404, not our validator
    r = await client.get(f"/api/v1/stock/{bad_ticker}")
    assert r.status_code in (400, 422), f"Expected 400/422 for '{bad_ticker}', got {r.status_code}"


@pytest.mark.parametrize("bad_ticker", ["TOOLONG", "1NVDA", "A!B"])
async def test_news_invalid_tickers(client, bad_ticker):
    r = await client.get(f"/api/v1/news/{bad_ticker}")
    assert r.status_code in (400, 422)


# ── POST /api/v1/analyse — validation ────────────────────────────────────────

async def test_analyse_invalid_ticker_returns_422(client):
    r = await client.post("/api/v1/analyse", json={"ticker": "INVALID123"})
    assert r.status_code == 422


async def test_analyse_empty_ticker_returns_422(client):
    r = await client.post("/api/v1/analyse", json={"ticker": ""})
    assert r.status_code == 422


async def test_analyse_missing_ticker_returns_422(client):
    r = await client.post("/api/v1/analyse", json={})
    assert r.status_code == 422


# ── Metrics ───────────────────────────────────────────────────────────────────

async def test_metrics_shape(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    body = r.json()
    assert "total_analyses" in body
    assert "popular_stocks" in body
    assert "decision_distribution" in body
    assert isinstance(body["popular_stocks"], list)


# ── History ───────────────────────────────────────────────────────────────────

async def test_history_returns_list(client):
    r = await client.get("/api/v1/history")
    assert r.status_code == 200
    body = r.json()
    assert "analyses" in body
    assert isinstance(body["analyses"], list)


async def test_history_limit_validation(client):
    r = await client.get("/api/v1/history?limit=0")
    assert r.status_code == 400

    r = await client.get("/api/v1/history?limit=101")
    assert r.status_code == 400


async def test_history_item_not_found(client):
    r = await client.get("/api/v1/history/999999")
    assert r.status_code == 404
