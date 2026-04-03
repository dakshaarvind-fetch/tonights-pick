"""Unit tests for mood_map — no network required."""
import pytest
from tonights_pick_mcp.mood_map import resolve_vibe, VIBE_MAP


def test_direct_vibe():
    result = resolve_vibe("on-edge")
    assert result == VIBE_MAP["on-edge"]
    assert 53 in result["genres"]  # thriller


def test_alias():
    result = resolve_vibe("tense")
    assert result == VIBE_MAP["on-edge"]


def test_partial_match():
    result = resolve_vibe("slow burn tension")
    assert result == VIBE_MAP["slow-burn"]


def test_unknown_vibe_fallback():
    result = resolve_vibe("quirky-surrealist")
    assert "genres" in result
    assert "sort" in result
    assert result["sort"] == "popularity.desc"


def test_case_insensitive():
    assert resolve_vibe("DARK") == resolve_vibe("dark")
