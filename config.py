"""Application configuration."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

REVIEWS_DB_PATH = DATA_DIR / "reviews.json"


def _get_config(key: str, default: str = "") -> str:
    """Read from env (.env) first, then Streamlit secrets (deploy)."""
    value = os.getenv(key, "").strip()
    if value:
        return value
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key]).strip()
    except Exception:
        pass
    return default


def get_groq_api_key() -> str:
    load_dotenv(BASE_DIR / ".env", override=True)
    return _get_config("GROQ_API_KEY")


def get_openai_api_key() -> str:
    load_dotenv(BASE_DIR / ".env", override=True)
    return _get_config("OPENAI_API_KEY")


def get_ai_provider() -> str:
    load_dotenv(BASE_DIR / ".env", override=True)
    return _get_config("AI_PROVIDER", "groq").lower()


def get_langsmith_api_key() -> str:
    load_dotenv(BASE_DIR / ".env", override=True)
    return _get_config("LANGSMITH_API_KEY") or _get_config("LANGCHAIN_API_KEY")


def get_langsmith_project() -> str:
    load_dotenv(BASE_DIR / ".env", override=True)
    return _get_config("LANGSMITH_PROJECT", "automated-code-reviewer")


def is_langsmith_enabled() -> bool:
    load_dotenv(BASE_DIR / ".env", override=True)
    val = _get_config("LANGSMITH_TRACING", "false").lower()
    return val in ("true", "1", "yes", "on")


# Backwards-compatible module-level reads (refreshed on import)
GROQ_API_KEY = get_groq_api_key()
OPENAI_API_KEY = get_openai_api_key()
AI_PROVIDER = get_ai_provider()

GROQ_MODEL = "llama-3.3-70b-versatile"
OPENAI_MODEL = "gpt-4o-mini"

MAX_CODE_CHARS = 120_000
MAX_FILES_PER_REVIEW = 25
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".cpp", ".c", ".h", ".cs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".sql", ".sh", ".bash", ".yaml", ".yml", ".json",
    ".html", ".css", ".scss", ".vue", ".r", ".m", ".lua",
}

PERSONALITIES = {
    "friendly_mentor": {
        "name": "Friendly Mentor",
        "icon": "🌟",
        "tone": "Supportive and educational. Explain concepts clearly, celebrate good patterns, and gently guide improvements.",
    },
    "strict_senior": {
        "name": "Strict Senior Engineer",
        "icon": "🔧",
        "tone": "Direct, uncompromising, and detail-oriented. No sugar-coating. Enforce best practices and production standards.",
    },
    "startup_cto": {
        "name": "Startup CTO",
        "icon": "🚀",
        "tone": "Pragmatic and velocity-focused. Balance quality with shipping speed. Prioritize ROI of fixes.",
    },
    "faang_reviewer": {
        "name": "FAANG Reviewer",
        "icon": "🏛️",
        "tone": "Bar-raiser standards. Focus on scalability, observability, edge cases, and system design implications.",
    },
}

SEVERITY_COLORS = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
    "info": "#64748b",
}

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
