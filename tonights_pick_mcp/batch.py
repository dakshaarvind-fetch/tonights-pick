"""Batch async operations — fires all provider checks simultaneously."""
from __future__ import annotations
import asyncio
from typing import Optional

from .tmdb_client import get_watch_providers_raw
from .models import WatchProvider, WatchProviderResult


def _parse_providers(raw: list[dict]) -> list[WatchProvider]:
    return [
        WatchProvider(
            provider_id=p["provider_id"],
            provider_name=p["provider_name"],
            logo_path=p.get("logo_path"),
        )
        for p in raw
    ]


async def _fetch_providers_for_movie(movie_id: int, country: str) -> WatchProviderResult:
    data = await get_watch_providers_raw(movie_id)
    results = data.get("results", {})
    country_data = results.get(country, {})

    return WatchProviderResult(
        movie_id=movie_id,
        country=country,
        flatrate=_parse_providers(country_data.get("flatrate", [])),
        rent=_parse_providers(country_data.get("rent", [])),
        buy=_parse_providers(country_data.get("buy", [])),
    )


async def batch_watch_providers(
    movie_ids: list[int],
    country: str = "US",
) -> list[WatchProviderResult]:
    """Fetch watch providers for all movie_ids simultaneously via asyncio.gather.

    Returns a list of WatchProviderResult in the same order as movie_ids.
    Failed lookups are returned as empty WatchProviderResult objects.
    """
    tasks = [_fetch_providers_for_movie(mid, country) for mid in movie_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: list[WatchProviderResult] = []
    for movie_id, result in zip(movie_ids, results):
        if isinstance(result, Exception):
            # Return empty result rather than crashing the whole batch
            out.append(WatchProviderResult(movie_id=movie_id, country=country))
        else:
            out.append(result)
    return out
