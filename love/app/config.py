"""Configuration for Love, loaded from environment (.env).

Model slugs are intentionally env-driven so you can swap them without code
changes. VERIFY the current slugs at https://openrouter.ai/models before you
rely on them — OpenRouter resolves aliases, but slugs do drift over time.
"""
import os

from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# Sent to OpenRouter for attribution/ranking (optional but recommended).
APP_TITLE = os.getenv("APP_TITLE", "Love")
SITE_URL = os.getenv("SITE_URL", "https://korgems.com")

# The starter routing table. Each route key maps to one OpenRouter slug.
# These are sensible defaults for mid-2026 — confirm them on /models.
MODELS = {
    "code": os.getenv("MODEL_CODE", "anthropic/claude-opus-4.6"),
    "reasoning": os.getenv("MODEL_REASONING", "openai/gpt-5"),
    "fast": os.getenv("MODEL_FAST", "google/gemini-2.5-flash"),
    "default": os.getenv("MODEL_DEFAULT", "google/gemini-2.5-pro"),
}
