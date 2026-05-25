"""LangSmith observability for AI code reviews."""
import os
from functools import wraps
from typing import Callable, Optional

from config import (
    get_langsmith_api_key,
    get_langsmith_project,
    is_langsmith_enabled,
)


def configure_langsmith() -> dict:
    """
    Apply LangSmith env vars so @traceable and LLM calls are logged.
    Call once at app startup and before each review.
    """
    enabled = is_langsmith_enabled()
    api_key = get_langsmith_api_key()
    project = get_langsmith_project()

    if enabled and api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGSMITH_PROJECT"] = project
        # Backwards-compatible aliases
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
    else:
        os.environ.pop("LANGSMITH_TRACING", None)
        os.environ.pop("LANGCHAIN_TRACING_V2", None)

    return get_langsmith_status()


def get_langsmith_status() -> dict:
    api_key = get_langsmith_api_key()
    return {
        "enabled": is_langsmith_enabled(),
        "configured": bool(api_key),
        "project": get_langsmith_project(),
        "active": is_langsmith_enabled() and bool(api_key),
    }


def maybe_trace(name: str, run_type: str = "chain"):
    """Decorator: wrap function with LangSmith @traceable when enabled."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            status = configure_langsmith()
            if not status["active"]:
                return fn(*args, **kwargs)
            try:
                from langsmith import traceable

                traced = traceable(name=name, run_type=run_type)(fn)
                return traced(*args, **kwargs)
            except Exception:
                return fn(*args, **kwargs)

        return wrapper

    return decorator
