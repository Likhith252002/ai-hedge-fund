"""
conftest.py
Shared pytest fixtures for the AI Hedge Fund test suite.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure the backend package root is on sys.path when running from project root
_BACKEND = Path(__file__).parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Point the DB at a temp file so tests never touch the real database
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    """Async HTTP client wired directly to the FastAPI app (no real network)."""
    from api.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
