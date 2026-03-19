"""
database.py
SQLite persistence layer for AI Hedge Fund analysis history.

Tables:
  analyses — one row per completed analysis run
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# DB lives one level up from the db/ package, under backend/data/
_DB_PATH = Path(__file__).parent.parent / "data" / "analyses.db"


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS analyses (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker            TEXT    NOT NULL,
    created_at        TEXT    NOT NULL,
    action            TEXT,
    confidence        INTEGER,
    position_size     REAL,
    quant_signal      TEXT,
    execution_time_ms INTEGER,
    result_json       TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ticker     ON analyses (ticker);
CREATE INDEX IF NOT EXISTS idx_created_at ON analyses (created_at);
CREATE INDEX IF NOT EXISTS idx_action     ON analyses (action);
"""


# ── Lifecycle ─────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Create tables and indexes if they don't already exist."""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.executescript(_DDL)
    logger.info("Database ready at %s", _DB_PATH)


# ── Write ─────────────────────────────────────────────────────────────────────

def save_analysis(
    ticker: str,
    result: Dict[str, Any],
    execution_time_ms: int,
) -> int:
    """Persist a completed analysis. Returns the new row id."""
    decision = result.get("decision") or {}
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO analyses
                (ticker, created_at, action, confidence, position_size,
                 quant_signal, execution_time_ms, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticker.upper(),
                datetime.utcnow().isoformat(),
                decision.get("action"),
                decision.get("confidence"),
                decision.get("position_size"),
                result.get("quant_signal"),
                execution_time_ms,
                json.dumps(result, default=str),
            ),
        )
        row_id = cur.lastrowid
    logger.info("Saved analysis id=%s for %s (%d ms)", row_id, ticker, execution_time_ms)
    return row_id


# ── Read ──────────────────────────────────────────────────────────────────────

def get_recent_analyses(limit: int = 20) -> List[Dict[str, Any]]:
    """Return the most recent analyses (summary fields only, no full JSON)."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, ticker, created_at, action, confidence,
                   position_size, quant_signal, execution_time_ms
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_analysis_by_id(analysis_id: int) -> Optional[Dict[str, Any]]:
    """Return a single analysis including the full result JSON."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()
    if not row:
        return None
    r = dict(row)
    r["result"] = json.loads(r.pop("result_json", "{}"))
    return r


def get_cached_analysis(
    ticker: str,
    max_age_hours: float = 24.0,
) -> Optional[Dict[str, Any]]:
    """
    Return the most recent analysis for *ticker* if it was run within the
    last *max_age_hours* hours; otherwise return None.
    """
    cutoff = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
    with _connect() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT * FROM analyses
            WHERE ticker = ? AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (ticker.upper(), cutoff),
        ).fetchone()
    if not row:
        return None
    r = dict(row)
    r["result"] = json.loads(r.pop("result_json", "{}"))
    return r


def get_metrics() -> Dict[str, Any]:
    """Aggregate stats for the /metrics endpoint."""
    with _connect() as conn:
        conn.row_factory = sqlite3.Row

        total = conn.execute(
            "SELECT COUNT(*) AS n FROM analyses"
        ).fetchone()["n"]

        avg_ms = conn.execute(
            "SELECT AVG(execution_time_ms) AS t FROM analyses"
        ).fetchone()["t"]

        popular = conn.execute(
            """
            SELECT ticker, COUNT(*) AS count
            FROM analyses
            GROUP BY ticker
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

        action_dist = conn.execute(
            """
            SELECT action, COUNT(*) AS count
            FROM analyses
            WHERE action IS NOT NULL
            GROUP BY action
            """
        ).fetchall()

        recent_7d = conn.execute(
            """
            SELECT COUNT(*) AS n FROM analyses
            WHERE created_at > ?
            """,
            ((datetime.utcnow() - timedelta(days=7)).isoformat(),),
        ).fetchone()["n"]

    return {
        "total_analyses":          total,
        "analyses_last_7_days":    recent_7d,
        "avg_execution_time_ms":   round(avg_ms) if avg_ms else None,
        "popular_stocks":          [dict(r) for r in popular],
        "decision_distribution":   {r["action"]: r["count"] for r in action_dist},
    }


# ── Internal ──────────────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    return sqlite3.connect(_DB_PATH, check_same_thread=False)
