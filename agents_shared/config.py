"""
Shared environment variable helpers for agents.
"""

from __future__ import annotations

import os


def get_str(key: str, default: str | None = None) -> str | None:
    return os.getenv(key, default)


def get_bool(key: str, default: bool = False) -> bool:
    val = (os.getenv(key) or "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


def get_float(key: str, default: float = 0.0) -> float:
    val = (os.getenv(key) or "").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        return default


def validate_required_env(keys: list[str]) -> list[str]:
    """Return a list of env var names that are missing or empty."""
    return [k for k in keys if not (os.getenv(k) or "").strip()]
