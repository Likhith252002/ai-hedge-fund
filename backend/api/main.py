"""
main.py
FastAPI application entry point for the AI Hedge Fund backend.
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title       = "AI Hedge Fund",
    description = "Multi-agent LangGraph hedge fund powered by Claude.",
    version     = "1.0.0",
)

_default_origins = "http://localhost:5173,http://localhost:4173"
_origins = os.getenv("ALLOWED_ORIGINS", _default_origins).split(",")
# allow_credentials cannot be True when allow_origins=["*"] (CORS spec restriction)
_wildcard = _origins == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins     = _origins,
    allow_credentials = not _wildcard,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

app.include_router(router)

logger.info("AI Hedge Fund backend ready.")
