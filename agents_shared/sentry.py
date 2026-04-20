"""
Shared Sentry helpers for agents.

Goals:
- Standard initialization with consistent tags
- Small helper functions for breadcrumbs and user context
"""

from __future__ import annotations

from typing import Any

from agents_shared.config import get_bool, get_float, get_str


def init_sentry(
    *,
    agent_name: str,
    agent_address: str | None = None,
    environment: str | None = None,
    traces_sample_rate: float | None = None,
    **extra_tags: Any,
) -> bool:
    """
    Initialize Sentry monitoring for an agent.

    Env vars:
    - SENTRY_ENABLED (default: false; must be true to enable)
    - SENTRY_DSN (required to enable)
    - SENTRY_ENVIRONMENT (default: production)
    - SENTRY_TRACES_SAMPLE_RATE (default: 0.1)
    """
    try:
        import sentry_sdk
        from sentry_sdk.integrations.asyncio import AsyncioIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
    except Exception:
        # Allow agents without sentry-sdk installed to run.
        return False

    if not get_bool("SENTRY_ENABLED", False):
        return False

    sentry_dsn = get_str("SENTRY_DSN")
    if not sentry_dsn:
        return False

    env = environment or get_str("SENTRY_ENVIRONMENT", "production") or "production"
    tsr = traces_sample_rate if traces_sample_rate is not None else get_float("SENTRY_TRACES_SAMPLE_RATE", 0.1)

    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=env,
        traces_sample_rate=tsr,
        profiles_sample_rate=tsr,
        integrations=[
            AsyncioIntegration(),
            LoggingIntegration(
                level=None,
                event_level=40,  # logging.ERROR
            ),
        ],
        attach_stacktrace=True,
        send_default_pii=False,
        max_breadcrumbs=50,
    )

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("agent_name", agent_name)
        if agent_address:
            scope.set_tag("agent_address", agent_address)
            scope.set_context("agent", {"name": agent_name, "address": agent_address})
        for k, v in extra_tags.items():
            scope.set_tag(k, v)

    return True


def capture_agent_error(error: Exception, extra_context: dict[str, Any] | None = None) -> None:
    try:
        import sentry_sdk
    except Exception:
        return

    with sentry_sdk.push_scope() as scope:
        if extra_context:
            for key, value in extra_context.items():
                scope.set_context(key, value)
        sentry_sdk.capture_exception(error)


def set_user_context(user_address: str, session_id: str | None = None) -> None:
    try:
        import sentry_sdk
    except Exception:
        return

    with sentry_sdk.configure_scope() as scope:
        scope.set_user({"id": user_address, "session_id": session_id})


def add_breadcrumb(
    *,
    message: str,
    category: str = "info",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    try:
        import sentry_sdk
    except Exception:
        return

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data or {},
    )
