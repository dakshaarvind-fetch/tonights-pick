"""Maps user-described vibes / moods to TMDB genre IDs and search keywords."""
from __future__ import annotations

# TMDB canonical genre IDs
GENRE_IDS = {
    "action": 28,
    "adventure": 12,
    "animation": 16,
    "comedy": 35,
    "crime": 80,
    "documentary": 99,
    "drama": 18,
    "family": 10751,
    "fantasy": 14,
    "history": 36,
    "horror": 27,
    "music": 10402,
    "mystery": 9648,
    "romance": 10749,
    "sci-fi": 878,
    "science fiction": 878,
    "thriller": 53,
    "war": 10752,
    "western": 37,
}

# Vibe → (genre_ids, keywords, sort_hint)
# sort_hint: "popularity.desc" | "vote_average.desc" | "release_date.desc"
VIBE_MAP: dict[str, dict] = {
    "on-edge": {
        "genres": [53, 80],          # thriller, crime
        "keywords": ["suspense", "tension"],
        "sort": "vote_average.desc",
    },
    "slow-burn": {
        "genres": [53, 18],          # thriller, drama
        "keywords": ["slow burn", "psychological"],
        "sort": "vote_average.desc",
    },
    "dark": {
        "genres": [27, 53, 80],      # horror, thriller, crime
        "keywords": ["dark", "disturbing"],
        "sort": "vote_average.desc",
    },
    "intense": {
        "genres": [28, 53],          # action, thriller
        "keywords": ["intense", "adrenaline"],
        "sort": "popularity.desc",
    },
    "feel-good": {
        "genres": [35, 10749],       # comedy, romance
        "keywords": ["uplifting", "heartwarming"],
        "sort": "popularity.desc",
    },
    "romantic": {
        "genres": [10749, 35],
        "keywords": ["romance", "love"],
        "sort": "vote_average.desc",
    },
    "cosy": {
        "genres": [35, 10751],       # comedy, family
        "keywords": ["cozy", "comfort"],
        "sort": "popularity.desc",
    },
    "mind-bending": {
        "genres": [878, 53],         # sci-fi, thriller
        "keywords": ["mindbending", "twist"],
        "sort": "vote_average.desc",
    },
    "scary": {
        "genres": [27],
        "keywords": ["scary", "terror"],
        "sort": "popularity.desc",
    },
    "funny": {
        "genres": [35],
        "keywords": ["comedy", "funny"],
        "sort": "popularity.desc",
    },
    "action-packed": {
        "genres": [28, 12],
        "keywords": ["action", "adventure"],
        "sort": "popularity.desc",
    },
    "tearjerker": {
        "genres": [18, 10749],
        "keywords": ["emotional", "tearjerker"],
        "sort": "vote_average.desc",
    },
}

# Aliases → canonical vibe keys
_ALIASES: dict[str, str] = {
    "tense": "on-edge",
    "edge of seat": "on-edge",
    "edge-of-seat": "on-edge",
    "gripping": "on-edge",
    "creepy": "dark",
    "gloomy": "dark",
    "chill": "cosy",
    "relaxing": "cosy",
    "happy": "feel-good",
    "light": "feel-good",
    "cute": "romantic",
    "love": "romantic",
    "exciting": "action-packed",
    "trippy": "mind-bending",
    "thought-provoking": "mind-bending",
    "sad": "tearjerker",
    "emotional": "tearjerker",
}


def resolve_vibe(vibe: str) -> dict:
    """Return genre IDs, keywords, and sort preference for a vibe string.

    Falls back to a generic popularity sort if the vibe is unrecognised.
    """
    key = vibe.lower().strip()
    # direct match
    if key in VIBE_MAP:
        return VIBE_MAP[key]
    # alias match
    if key in _ALIASES:
        return VIBE_MAP[_ALIASES[key]]
    # partial match — normalise hyphens to spaces for comparison
    key_norm = key.replace("-", " ")
    for canonical in VIBE_MAP:
        canonical_norm = canonical.replace("-", " ")
        if canonical_norm in key_norm or key_norm in canonical_norm:
            return VIBE_MAP[canonical]
    # fallback: return drama + popularity
    return {
        "genres": [18],
        "keywords": [key],
        "sort": "popularity.desc",
    }
