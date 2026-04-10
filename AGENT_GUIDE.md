# Tonight's Pick — Agentverse Agent Guide

This guide explains what the **Tonight's Pick** uAgent does, what messages it accepts, and how to interact with it from another agent or from the Agentverse chat interface.

---

## Overview

Tonight's Pick is a movie and TV recommendation agent. Send it a plain-English request and it will query TMDB to return tailored recommendations — including streaming availability for your country.

The agent understands mood-based queries, title searches, trending lookups, and watch provider checks. It is designed to be used conversationally: ask follow-up questions, refine by mood or runtime, or ask what's available on a specific platform.

---

## What you can ask

### Mood / vibe discovery

Ask the agent to find something based on how you feel right now.

```
Find me something dark and slow-burn to watch tonight
I want a feel-good comedy, nothing too long
Something mind-bending — I love psychological thrillers
Recommend a cosy TV show for the weekend
```

Supported moods: `on-edge`, `slow-burn`, `dark`, `intense`, `feel-good`, `romantic`, `cosy`, `mind-bending`, `scary`, `funny`, `action-packed`, `tearjerker`

Aliases also work: *tense*, *gripping*, *chill*, *relaxing*, *happy*, *trippy*, *sad*, *emotional*, *exciting*, and more.

### Title search

```
Search for movies like Parasite
Find the TV show Breaking Bad
What movies has Christopher Nolan directed?
```

### Trending

```
What's trending on movies this week?
Show me the most popular TV shows right now
```

### Similar titles

```
Find movies similar to Interstellar
What shows are similar to Succession?
```

### Streaming availability

```
Which of those are on Netflix in the US?
Check what's available to stream in the UK
Is it available to rent or buy?
```

### Runtime filter

```
Something feel-good but under 90 minutes
Short films only — max 80 minutes
```

---

## Message format

Send plain-text messages in natural language. The agent will interpret your request, call the appropriate TMDB tools, and respond with a formatted list of recommendations.

No structured schema is required — just describe what you want.

---

## Response format

The agent responds with a curated list of recommendations. Each entry includes:

- **Title** and release year
- **Rating** (TMDB score out of 10)
- **Overview** (brief plot summary)
- **Streaming availability** for your country (subscription, rent, or buy)

Example response:

```
Here are some dark, slow-burn picks for tonight:

1. Prisoners (2013) ★ 8.1
   A desperate father takes the law into his own hands when his daughter goes missing.
   Streaming: Max

2. Zodiac (2007) ★ 7.7
   The true story of the hunt for the Zodiac Killer in San Francisco.
   Streaming: Not available — Rent on Amazon, Apple TV

3. No Country for Old Men (2007) ★ 8.2
   A hunter stumbles upon a drug deal gone wrong and must outrun a relentless killer.
   Streaming: Paramount+
```

---

## Capabilities summary

| Capability | Example prompt |
|---|---|
| Mood-based movie discovery | "Something on-edge and intense" |
| Mood-based TV discovery | "A cosy TV show for tonight" |
| Title search (movies) | "Find movies called The Batman" |
| Title search (TV) | "Search for the show Severance" |
| Trending movies / TV | "What's trending this week?" |
| Similar movies | "Movies like Inception" |
| Similar TV shows | "Shows like The Wire" |
| Full movie details | "Tell me more about movie ID 27205" |
| Full TV details | "Details for show ID 1396" |
| Keyword search | "Movies tagged with heist or revenge" |
| Watch providers (movies) | "Which of those are streaming in Australia?" |
| Watch providers (TV) | "Is that show available in the UK?" |
| Runtime filter | "Keep it under 90 minutes" |

---

## Country codes

When asking about streaming availability, you can specify a country using its ISO 3166-1 alpha-2 code:

| Country | Code |
|---|---|
| United States | US |
| United Kingdom | GB |
| India | IN |
| Australia | AU |
| Canada | CA |
| Germany | DE |
| France | FR |

Default country is **US** if not specified.

---

## Tips

- Start with a mood or vibe — the agent will pick the best genre mix and sort strategy automatically.
- After getting a list, follow up with *"which of those are on Netflix?"* to filter by platform.
- Add *"under 90 minutes"* or *"under 2 hours"* to any movie query to filter by runtime.
- Use *"movie"* or *"show"* / *"TV"* in your query to target the right media type.
- The agent handles typos and partial matches on mood names gracefully.

---

## Powered by

- [TMDB](https://www.themoviedb.org/) — movie and TV metadata, ratings, and watch providers
- [Fetch.ai uAgents](https://fetch.ai/) — agent communication and Agentverse hosting
- [FastMCP](https://github.com/jlowin/fastmcp) — MCP server transport for Claude Desktop / Google ADK
