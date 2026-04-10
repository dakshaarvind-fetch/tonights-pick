# Tonight's Pick

You open Netflix. You scroll for 20 minutes. You watch nothing.

Tonight's Pick fixes that. It's a conversational AI agent that takes how you're feeling right now — *"I want something dark and slow-burn"*, *"something feel-good, nothing too long"* — and returns actual picks with real streaming availability for your country. No more genre rabbit holes, no more decision fatigue.

---

## Why it exists

Streaming platforms optimise for engagement, not for helping you find the right film. Search requires you to already know what you want. Recommendation engines recycle what you've already seen. Mood-based browsing barely exists.

Tonight's Pick is built around the one piece of information you always have: how you feel right now. Describe your vibe in plain English, optionally mention what you loved last, and the agent does the rest — querying TMDB, filtering by quality signals, and checking what's actually available to stream in your country.

It's useful as a standalone conversational agent and as a tool layer that any AI assistant can call via the Model Context Protocol.

---

## How it works

The core is a **FastMCP server** that exposes TMDB as a set of typed async tools. When a user describes what they want, the agent:

1. Maps the mood or vibe to TMDB genre IDs and a sort strategy (e.g. *"slow-burn"* → Drama + Thriller, sorted by vote average)
2. Queries TMDB's discover, search, trending, or keyword endpoints
3. Fires concurrent watch-provider lookups for all candidate titles via `asyncio.gather`
4. Returns a ranked list with streaming, rent, and buy availability per title

The mood-mapping layer (`mood_map.py`) handles direct vibe names, aliases (*tense*, *gripping*, *chill*, *trippy*), and partial fuzzy matches — so users don't need to know the exact supported terms.

The same tool functions are dual-purpose: decorated with `@mcp.tool()` for MCP server use, and importable as plain async functions for the Fetch.ai uAgent runtime.

---

## MCP Server Integration

Tonight's Pick runs as an MCP server over stdio, making it compatible with **Claude Desktop** and **Google ADK** out of the box.

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tonights-pick": {
      "command": "tonights-pick-mcp",
      "env": {
        "TMDB_API_KEY": "your_tmdb_api_key_here"
      }
    }
  }
}
```

Claude will automatically discover all 13 tools and can call them mid-conversation to answer questions like *"what's trending this week?"* or *"is Parasite on Netflix in the UK?"* without any additional prompt engineering.

---

## Architecture

```
tonights_pick_mcp/
├── server.py        # FastMCP entry point — runs stdio MCP server
├── tools.py         # 13 @mcp.tool() async functions (movies + TV)
├── tmdb_client.py   # Raw async TMDB HTTP client (httpx)
├── batch.py         # Concurrent watch-provider lookups via asyncio.gather
├── mood_map.py      # Vibe → TMDB genre IDs + sort strategy + aliases
└── models.py        # Pydantic models for TMDB API responses
```

### Tools exposed

| Tool | What it does |
|---|---|
| `search_movies` | Search by movie title, returns TMDB ID + metadata |
| `search_tv` | Search by TV show title |
| `get_movie_details` | Full details — runtime, genres, tagline, rating |
| `get_tv_details` | Full details — seasons, episode count, status |
| `get_similar` | Movies similar to a given TMDB ID |
| `get_similar_tv` | TV shows similar to a given TMDB ID |
| `get_recommendations` | TMDB behavioural recommendations for a movie |
| `get_trending` | Trending movies or TV by day or week |
| `resolve_mood` | Mood → movie discovery (genre + quality filtered) |
| `resolve_mood_tv` | Mood → TV show discovery |
| `search_by_keyword` | TMDB keyword tag search (heist, revenge, road-trip…) |
| `check_watch_providers` | Streaming availability for a list of movie IDs |
| `check_tv_watch_providers` | Streaming availability for a list of TV show IDs |

---

## Example prompts

```
I want something dark and slow-burn tonight

Find me a feel-good comedy, nothing over 90 minutes

What's trending in movies this week?

Something mind-bending — I loved Inception and Annihilation

Find shows similar to Succession

Which of those are streaming in the UK?
```

Supported moods: `on-edge` · `slow-burn` · `dark` · `intense` · `feel-good` · `romantic` · `cosy` · `mind-bending` · `scary` · `funny` · `action-packed` · `tearjerker`

---

## Installation

**Prerequisites:** Python 3.11+, a free [TMDB API key](https://www.themoviedb.org/settings/api)

```bash
git clone https://github.com/your-username/tonights-pick.git
cd tonights-pick

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .
```

Create a `.env` file in the project root:

```
TMDB_API_KEY=your_tmdb_api_key_here
```

Run the MCP server:

```bash
tonights-pick-mcp
```

Or install into Claude Desktop using the config block above and restart Claude.

---

## Docker

Docker config lives in `docker/`. Run the agent container from the repo root:

```bash
docker compose -f docker/docker-compose.yml up --build
```

The build context is the repo root so `tonights_pick_mcp/` and `agent/` are both available inside the image.

---

## Agentverse (Fetch.ai)

Tonight's Pick also runs as a uAgent on Fetch.ai's Agentverse. See [AGENT_GUIDE.md](AGENT_GUIDE.md) for the full interaction guide, message schema, and deployment notes.

---

## License

MIT
