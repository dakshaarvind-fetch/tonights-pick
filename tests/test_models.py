"""Unit tests for Pydantic models — no network required."""
import pytest
from tonights_pick_mcp.models import MovieResult, WatchProviderResult, WatchProvider


def test_movie_result_year():
    m = MovieResult(id=1, title="Parasite", release_date="2019-05-30")
    assert m.year == "2019"


def test_movie_result_missing_date():
    m = MovieResult(id=2, title="Unknown")
    assert m.year == "N/A"


def test_watch_provider_streaming_names():
    providers = [
        WatchProvider(provider_id=8, provider_name="Netflix"),
        WatchProvider(provider_id=9, provider_name="Amazon Prime Video"),
    ]
    result = WatchProviderResult(movie_id=496243, country="US", flatrate=providers)
    assert result.streaming_names == ["Netflix", "Amazon Prime Video"]


def test_watch_provider_empty():
    result = WatchProviderResult(movie_id=1, country="US")
    assert result.streaming_names == []
