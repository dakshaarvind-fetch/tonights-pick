"""Raw async HTTP client for the TMDB REST API (v3)."""
from __future__ import annotations
import os
from typing import Any

import httpx

BASE_URL = "https://api.themoviedb.org/3"
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        api_key = os.environ.get("TMDB_API_KEY", "")
        if not api_key:
            raise RuntimeError("TMDB_API_KEY environment variable is not set")
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            params={"api_key": api_key},
            timeout=10.0,
        )
    return _client


async def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a GET request to the TMDB API and return the parsed JSON."""
    client = _get_client()
    resp = await client.get(path, params=params or {})
    resp.raise_for_status()
    return resp.json()


async def search_movies_raw(query: str, page: int = 1) -> dict[str, Any]:
    return await _get("/search/movie", {"query": query, "page": page})


async def get_movie_details_raw(movie_id: int) -> dict[str, Any]:
    return await _get(f"/movie/{movie_id}")


async def get_similar_movies_raw(movie_id: int, page: int = 1) -> dict[str, Any]:
    return await _get(f"/movie/{movie_id}/similar", {"page": page})


async def get_recommendations_raw(movie_id: int, page: int = 1) -> dict[str, Any]:
    return await _get(f"/movie/{movie_id}/recommendations", {"page": page})


async def get_trending_raw(media_type: str = "movie", window: str = "week") -> dict[str, Any]:
    return await _get(f"/trending/{media_type}/{window}")


async def discover_movies_raw(params: dict[str, Any]) -> dict[str, Any]:
    return await _get("/discover/movie", params)


async def get_watch_providers_raw(movie_id: int) -> dict[str, Any]:
    return await _get(f"/movie/{movie_id}/watch/providers")


async def search_by_keyword_raw(keyword: str) -> dict[str, Any]:
    return await _get("/search/keyword", {"query": keyword})


# ---------------------------------------------------------------------------
# TV endpoints
# ---------------------------------------------------------------------------

async def search_tv_raw(query: str, page: int = 1) -> dict[str, Any]:
    return await _get("/search/tv", {"query": query, "page": page})


async def get_tv_details_raw(tv_id: int) -> dict[str, Any]:
    return await _get(f"/tv/{tv_id}")


async def get_similar_tv_raw(tv_id: int, page: int = 1) -> dict[str, Any]:
    return await _get(f"/tv/{tv_id}/similar", {"page": page})


async def get_tv_recommendations_raw(tv_id: int, page: int = 1) -> dict[str, Any]:
    return await _get(f"/tv/{tv_id}/recommendations", {"page": page})


async def discover_tv_raw(params: dict[str, Any]) -> dict[str, Any]:
    return await _get("/discover/tv", params)


async def get_tv_watch_providers_raw(tv_id: int) -> dict[str, Any]:
    return await _get(f"/tv/{tv_id}/watch/providers")


async def aclose() -> None:
    """Close the shared HTTP client."""
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None
