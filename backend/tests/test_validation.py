"""
test_validation.py
Unit tests for ticker validation logic and rate-limiter helpers.
"""

from __future__ import annotations

import re
import pytest

_TICKER_RE = re.compile(r"^[A-Z]{1,5}$")


# ── Ticker regex ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("ticker", ["NVDA", "AAPL", "TSLA", "A", "GOOGL"])
def test_valid_tickers_pass(ticker):
    assert _TICKER_RE.match(ticker)


@pytest.mark.parametrize("ticker", [
    "nvda",          # lowercase
    "TOOLONG",       # 6 chars
    "123",           # digits
    "AA1",           # mixed
    "A B",           # space
    "",              # empty
    "A!",            # special char
    "AAAAAA",        # 6 chars
])
def test_invalid_tickers_fail(ticker):
    assert not _TICKER_RE.match(ticker)


# ── Pydantic model validation ─────────────────────────────────────────────────

def test_analysis_request_normalises_ticker():
    """AnalysisRequest should upper-case and validate the ticker field."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from api.routes import AnalysisRequest

    req = AnalysisRequest(ticker="nvda")
    assert req.ticker == "NVDA"


def test_analysis_request_rejects_bad_ticker():
    from pydantic import ValidationError
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from api.routes import AnalysisRequest

    with pytest.raises(ValidationError):
        AnalysisRequest(ticker="TOOLONG123")
