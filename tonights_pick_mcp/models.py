"""Pydantic models for TMDB API responses."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class MovieResult(BaseModel):
    id: int
    title: str
    overview: str = ""
    release_date: str = ""
    vote_average: float = 0.0
    genre_ids: list[int] = Field(default_factory=list)
    popularity: float = 0.0

    @property
    def year(self) -> str:
        return self.release_date[:4] if self.release_date else "N/A"


class TVResult(BaseModel):
    id: int
    name: str
    overview: str = ""
    first_air_date: str = ""
    vote_average: float = 0.0
    genre_ids: list[int] = Field(default_factory=list)
    popularity: float = 0.0

    @property
    def year(self) -> str:
        return self.first_air_date[:4] if self.first_air_date else "N/A"


class WatchProvider(BaseModel):
    provider_id: int
    provider_name: str
    logo_path: Optional[str] = None


class WatchProviderResult(BaseModel):
    movie_id: int
    country: str
    flatrate: list[WatchProvider] = Field(default_factory=list)   # subscription streaming
    rent: list[WatchProvider] = Field(default_factory=list)
    buy: list[WatchProvider] = Field(default_factory=list)

    @property
    def streaming_names(self) -> list[str]:
        return [p.provider_name for p in self.flatrate]


class SearchResponse(BaseModel):
    results: list[MovieResult] = Field(default_factory=list)
    total_results: int = 0
    total_pages: int = 0
