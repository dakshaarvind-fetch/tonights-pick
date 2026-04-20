"""
Minimal HTTP health/readiness server for Kubernetes probes.

We keep this separate from the agent's main protocol port. Probes can hit the
health server over localhost inside the pod.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

from aiohttp import web

from agents_shared.config import validate_required_env


@dataclass(frozen=True, slots=True)
class HealthConfig:
    port: int
    required_env: tuple[str, ...]


_READY_EVENT = asyncio.Event()


def mark_ready() -> None:
    _READY_EVENT.set()


async def _healthz(_request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def _readyz(_request: web.Request) -> web.Response:
    missing = validate_required_env(list(_CONFIG.required_env))
    if missing:
        return web.json_response({"ok": False, "missing_env": missing}, status=503)
    if not _READY_EVENT.is_set():
        return web.json_response({"ok": False, "reason": "starting"}, status=503)
    return web.json_response({"ok": True})


_CONFIG = HealthConfig(
    port=int(os.getenv("HEALTH_PORT", "8080")),
    required_env=tuple(
        x.strip()
        for x in (os.getenv("REQUIRED_ENV_FOR_READY", "") or "").split(",")
        if x.strip()
    ),
)


async def start_health_server(config: HealthConfig | None = None) -> None:
    """
    Start the health server in the current event loop.

    Safe to call from an agent startup hook (spawns background task).
    """
    cfg = config or _CONFIG
    app = web.Application()
    app.router.add_get("/healthz", _healthz)
    app.router.add_get("/readyz", _readyz)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=cfg.port)
    try:
        await site.start()
    except OSError as e:
        # Avoid noisy "Task exception was never retrieved" when multiple agents run locally
        # and accidentally share the same HEALTH_PORT.
        # In Kubernetes each pod has its own network namespace, so this is typically not an issue.
        print(f"[health] failed to bind 0.0.0.0:{cfg.port} ({e}). Set HEALTH_PORT to a free port.")
        return
