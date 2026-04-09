"""MCP tool definitions — async functions decorated with @mcp.tool().

These functions are used two ways:
  1. By the FastMCP server (server.py) for local dev via Google ADK / Claude Desktop.
  2. Imported directly by the uAgent (agent/agent.py) which calls them as plain
     async functions — the @mcp.tool() decoration is ignored in that context.
"""
from __future__ import annotations
import json
from typing import Optional

from fastmcp import FastMCP

from .tmdb_client import (
    search_movies_raw,
    get_similar_movies_raw,
    get_recommendations_raw,
    get_trending_raw,
    discover_movies_raw,
    search_by_keyword_raw,
    get_movie_details_raw,
    search_tv_raw,
    get_tv_details_raw,
    get_similar_tv_raw,
    discover_tv_raw,
)
from .models import MovieResult, TVResult, SearchResponse
from .mood_map import resolve_vibe
from .batch import batch_watch_providers as _batch_watch_providers
from .batch import batch_tv_watch_providers as _batch_tv_watch_providers

mcp = FastMCP("tonights-pick-mcp")


def _tv_from_dict(d: dict) -> TVResult:
    return TVResult(
        id=d["id"],
        name=d.get("name", ""),
        overview=d.get("overview", ""),
        first_air_date=d.get("first_air_date", ""),
        vote_average=d.get("vote_average", 0.0),
        genre_ids=d.get("genre_ids", []),
        popularity=d.get("popularity", 0.0),
    )


def _format_tv(shows: list[TVResult], limit: int = 10) -> str:
    return json.dumps(
        [
            {
                "id": s.id,
                "title": s.name,
                "year": s.year,
                "rating": round(s.vote_average, 1),
                "overview": s.overview[:200],
            }
            for s in shows[:limit]
        ],
        indent=2,
    )


def _movie_from_dict(d: dict) -> MovieResult:
    return MovieResult(
        id=d["id"],
        title=d.get("title", ""),
        overview=d.get("overview", ""),
        release_date=d.get("release_date", ""),
        vote_average=d.get("vote_average", 0.0),
        genre_ids=d.get("genre_ids", []),
        popularity=d.get("popularity", 0.0),
    )


def _format_movies(movies: list[MovieResult], limit: int = 10) -> str:
    """Serialise a list of MovieResult objects to a compact JSON string."""
    return json.dumps(
        [
            {
                "id": m.id,
                "title": m.title,
                "year": m.year,
                "rating": round(m.vote_average, 1),
                "overview": m.overview[:200],
            }
            for m in movies[:limit]
        ],
        indent=2,
    )


@mcp.tool()
async def search_movies(query: str, limit: int = 5) -> str:
    """Search TMDB for movies matching a title or partial title.

    Returns up to `limit` results with id, title, year, rating, and overview.
    Use this to resolve a movie title to its TMDB ID before calling get_similar
    or batch_watch_providers.
    """
    data = await search_movies_raw(query)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def get_similar(movie_id: int, limit: int = 10) -> str:
    """Get movies similar to a given TMDB movie ID.

    Returns up to `limit` results. Use after search_movies to resolve an ID.
    """
    data = await get_similar_movies_raw(movie_id)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def get_recommendations(movie_id: int, limit: int = 10) -> str:
    """Get TMDB personalised recommendations for a given movie ID.

    Broader than get_similar — factors in user-behaviour signals.
    """
    data = await get_recommendations_raw(movie_id)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def resolve_mood(vibe: str, limit: int = 10, max_runtime: Optional[int] = None) -> str:
    """Discover movies that match a mood or vibe description.

    Supported vibes include: on-edge, slow-burn, dark, intense, feel-good,
    romantic, cosy, mind-bending, scary, funny, action-packed, tearjerker.
    Partial matches and common aliases are handled automatically.

    max_runtime: optional upper bound on runtime in minutes (e.g. 90).
    Returns up to `limit` movies sorted by the vibe's preferred signal.
    """
    mapping = resolve_vibe(vibe)
    genre_str = ",".join(str(g) for g in mapping["genres"])

    params: dict = {
        "with_genres": genre_str,
        "sort_by": mapping["sort"],
        "vote_count.gte": 200,
        "page": 1,
    }
    if max_runtime:
        params["with_runtime.lte"] = max_runtime
    data = await discover_movies_raw(params)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def get_trending(media_type: str = "movie", window: str = "week", limit: int = 10) -> str:
    """Fetch trending movies or TV shows from TMDB.

    media_type: "movie" or "tv"
    window: "day" or "week"

    Use this as a freshness signal — trending titles are more likely to be
    available on streaming and familiar to the user.
    """
    data = await get_trending_raw(media_type, window)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def search_by_keyword(keyword: str, limit: int = 10) -> str:
    """Find movies tagged with a specific keyword on TMDB.

    More precise than a text search — useful for vibes like 'psychological',
    'heist', 'revenge', 'road-trip', etc.

    Returns up to `limit` movies sorted by popularity.
    """
    # Step 1: resolve keyword string to a TMDB keyword ID
    kw_data = await search_by_keyword_raw(keyword)
    kw_results = kw_data.get("results", [])
    if not kw_results:
        return json.dumps([])

    keyword_id = kw_results[0]["id"]

    # Step 2: discover movies with that keyword
    params = {
        "with_keywords": keyword_id,
        "sort_by": "popularity.desc",
        "vote_count.gte": 100,
    }
    data = await discover_movies_raw(params)
    movies = [_movie_from_dict(d) for d in data.get("results", [])]
    return _format_movies(movies, limit)


@mcp.tool()
async def get_movie_details(movie_id: int) -> str:
    """Get full details for a single movie by TMDB ID.

    Returns title, year, runtime, genres, overview, tagline, and rating.
    """
    data = await get_movie_details_raw(movie_id)
    genres = [g["name"] for g in data.get("genres", [])]
    result = {
        "id": data["id"],
        "title": data.get("title", ""),
        "year": (data.get("release_date", "") or "")[:4],
        "runtime_min": data.get("runtime"),
        "rating": round(data.get("vote_average", 0.0), 1),
        "genres": genres,
        "tagline": data.get("tagline", ""),
        "overview": data.get("overview", ""),
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# TV tools
# ---------------------------------------------------------------------------

# TV genre IDs differ from movie genre IDs on TMDB
_TV_VIBE_MAP: dict[str, dict] = {
    "on-edge":       {"genres": [9648, 80],    "sort": "vote_average.desc"},   # mystery, crime
    "slow-burn":     {"genres": [18, 9648],    "sort": "vote_average.desc"},   # drama, mystery
    "dark":          {"genres": [80, 18],      "sort": "vote_average.desc"},   # crime, drama
    "intense":       {"genres": [10759, 18],   "sort": "popularity.desc"},     # action&adventure, drama
    "feel-good":     {"genres": [35, 10751],   "sort": "popularity.desc"},     # comedy, family
    "romantic":      {"genres": [18, 35],      "sort": "vote_average.desc"},   # drama, comedy
    "cosy":          {"genres": [35, 10751],   "sort": "popularity.desc"},     # comedy, family
    "mind-bending":  {"genres": [10765, 9648], "sort": "vote_average.desc"},   # sci-fi & fantasy, mystery
    "scary":         {"genres": [10765, 9648], "sort": "popularity.desc"},     # sci-fi & fantasy, mystery
    "funny":         {"genres": [35],          "sort": "popularity.desc"},     # comedy
    "action-packed": {"genres": [10759, 10765],"sort": "popularity.desc"},     # action&adventure, sci-fi
    "tearjerker":    {"genres": [18],          "sort": "vote_average.desc"},   # drama
}


@mcp.tool()
async def search_tv(query: str, limit: int = 5) -> str:
    """Search TMDB for TV shows matching a title or partial title.

    Returns up to `limit` results with id, title, year, rating, and overview.
    Use this to resolve a show title to its TMDB ID before calling get_similar_tv.
    """
    data = await search_tv_raw(query)
    shows = [_tv_from_dict(d) for d in data.get("results", [])]
    return _format_tv(shows, limit)


@mcp.tool()
async def get_similar_tv(tv_id: int, limit: int = 10) -> str:
    """Get TV shows similar to a given TMDB show ID."""
    data = await get_similar_tv_raw(tv_id)
    shows = [_tv_from_dict(d) for d in data.get("results", [])]
    return _format_tv(shows, limit)


@mcp.tool()
async def get_tv_details(tv_id: int) -> str:
    """Get full details for a TV show by TMDB ID.

    Returns title, year, number of seasons, episode runtime, genres, overview.
    """
    data = await get_tv_details_raw(tv_id)
    genres = [g["name"] for g in data.get("genres", [])]
    runtimes = data.get("episode_run_time", [])
    result = {
        "id": data["id"],
        "title": data.get("name", ""),
        "year": (data.get("first_air_date", "") or "")[:4],
        "seasons": data.get("number_of_seasons"),
        "episodes": data.get("number_of_episodes"),
        "episode_runtime_min": runtimes[0] if runtimes else None,
        "rating": round(data.get("vote_average", 0.0), 1),
        "genres": genres,
        "overview": data.get("overview", ""),
        "status": data.get("status", ""),
    }
    return json.dumps(result, indent=2)


@mcp.tool()
async def resolve_mood_tv(vibe: str, limit: int = 10) -> str:
    """Discover TV shows that match a mood or vibe.

    Supported vibes: on-edge, slow-burn, dark, intense, feel-good,
    romantic, cosy, mind-bending, scary, funny, action-packed, tearjerker.
    """
    key = vibe.lower().strip()
    mapping = _TV_VIBE_MAP.get(key, {"genres": [18], "sort": "popularity.desc"})
    genre_str = ",".join(str(g) for g in mapping["genres"])

    params: dict = {
        "with_genres": genre_str,
        "sort_by": mapping["sort"],
        "vote_count.gte": 100,
        "page": 1,
    }
    data = await discover_tv_raw(params)
    shows = [_tv_from_dict(d) for d in data.get("results", [])]
    return _format_tv(shows, limit)


@mcp.tool()
async def check_tv_watch_providers(tv_ids: list[int], country: str = "US") -> str:
    """Check streaming availability for a list of TV show IDs.

    country: ISO 3166-1 alpha-2 code, e.g. "US", "GB".
    Returns streaming, rent, and buy options per show.
    """
    results = await _batch_tv_watch_providers(tv_ids, country)
    output = []
    for r in results:
        entry: dict = {"tv_id": r.movie_id, "streaming": r.streaming_names}
        if not r.streaming_names:
            entry["rent"] = [p.provider_name for p in r.rent]
            entry["buy"] = [p.provider_name for p in r.buy]
        output.append(entry)
    return json.dumps(output, indent=2)


@mcp.tool()
async def check_watch_providers(movie_ids: list[int], country: str = "US") -> str:
    """Check streaming availability for a list of movie IDs in a given country.

    Fires all provider lookups simultaneously (asyncio.gather).
    country: ISO 3166-1 alpha-2 code, e.g. "US", "GB", "IN", "AU".

    Returns a JSON list — each entry has movie_id and a list of streaming
    service names where the film is available on subscription (flatrate).
    Also includes rent/buy options if no flatrate is available.
    """
    results = await _batch_watch_providers(movie_ids, country)
    output = []
    for r in results:
        entry: dict = {"movie_id": r.movie_id, "streaming": r.streaming_names}
        if not r.streaming_names:
            entry["rent"] = [p.provider_name for p in r.rent]
            entry["buy"] = [p.provider_name for p in r.buy]
        output.append(entry)
    return json.dumps(output, indent=2)
