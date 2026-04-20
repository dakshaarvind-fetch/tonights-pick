"""
Async PostgreSQL helpers for persistent user data (watchlist, seen titles).
Uses a connection pool backed by Supabase (transaction pooler, port 6543).
"""

from __future__ import annotations

import asyncpg

from agents_shared.config import get_str

_pool: asyncpg.Pool | None = None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        database_url = get_str("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL env var is not set")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5,
            statement_cache_size=0,  # required for Supabase transaction pooler
        )
        await _init_schema(_pool)
    return _pool


async def _init_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id  TEXT NOT NULL,
                title    TEXT NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (user_id, title)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_titles (
                user_id  TEXT NOT NULL,
                title    TEXT NOT NULL,
                added_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (user_id, title)
            )
        """)


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------


async def get_watchlist(user_id: str) -> list[str]:
    pool = await _get_pool()
    rows = await pool.fetch(
        "SELECT title FROM watchlist WHERE user_id = $1 ORDER BY added_at",
        user_id,
    )
    return [r["title"] for r in rows]


async def add_to_watchlist(user_id: str, title: str) -> None:
    pool = await _get_pool()
    await pool.execute(
        "INSERT INTO watchlist (user_id, title) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        user_id,
        title,
    )


# ---------------------------------------------------------------------------
# Seen titles
# ---------------------------------------------------------------------------


async def get_seen_titles(user_id: str) -> list[str]:
    pool = await _get_pool()
    rows = await pool.fetch(
        "SELECT title FROM seen_titles WHERE user_id = $1 ORDER BY added_at",
        user_id,
    )
    return [r["title"] for r in rows]


async def add_seen_title(user_id: str, title: str) -> None:
    pool = await _get_pool()
    await pool.execute(
        "INSERT INTO seen_titles (user_id, title) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        user_id,
        title,
    )


async def bulk_add_seen_titles(user_id: str, titles: list[str]) -> None:
    """Upsert multiple seen titles at once (used when intake parsing picks them up)."""
    if not titles:
        return
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO seen_titles (user_id, title) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            [(user_id, t) for t in titles],
        )
