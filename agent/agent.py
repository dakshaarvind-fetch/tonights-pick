"""Tonight's Pick — uAgent deployed on Fetch.ai Agentverse.

Conversation flow:
  1. User describes mood/context.
  2. Agent asks one follow-up (vibe + reference movie) if intake incomplete.
  3. Agent calls ASI1-mini with tool schemas; executes the tool-use loop.
  4. Agent replies with 3-4 picks grouped by vibe.

Session state stored in ctx.storage:
  vibe        — e.g. "on-edge"
  who         — e.g. "partner", "solo", "family"
  reference   — e.g. "Parasite"
  rejections  — JSON list of movie IDs the user has rejected
  history     — JSON list of {role, content} conversation turns
"""
from __future__ import annotations
import json
import os
import asyncio
from typing import Any

from uagents import Agent, Context, Protocol
from uagents.setup import fund_agent_if_low

# ASI1 client — OpenAI-compatible
from openai import AsyncOpenAI

# MCP tools imported directly as Python functions
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from tonights_pick_mcp.tools import (
    search_movies,
    get_similar,
    get_recommendations,
    resolve_mood,
    get_trending,
    search_by_keyword,
    get_movie_details,
    check_watch_providers,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ASI1_API_KEY = os.environ.get("ASI1_API_KEY", "")
ASI1_BASE_URL = "https://api.asi1.ai/v1"
ASI1_MODEL = "asi1-mini"
AGENT_SEED = os.environ.get("AGENT_SEED", "tonights-pick-agent-seed-v1")
AGENT_PORT = int(os.environ.get("AGENT_PORT", 8001))

asi1_client = AsyncOpenAI(api_key=ASI1_API_KEY, base_url=ASI1_BASE_URL)

# ---------------------------------------------------------------------------
# Tool registry — maps tool name → callable
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS: dict[str, Any] = {
    "search_movies": search_movies,
    "get_similar": get_similar,
    "get_recommendations": get_recommendations,
    "resolve_mood": resolve_mood,
    "get_trending": get_trending,
    "search_by_keyword": search_by_keyword,
    "get_movie_details": get_movie_details,
    "check_watch_providers": check_watch_providers,
}

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "search_movies",
            "description": "Search TMDB for movies matching a title. Use to resolve a title to its TMDB ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Movie title or partial title"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_similar",
            "description": "Get movies similar to a given TMDB movie ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": "Get TMDB personalised recommendations for a movie ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resolve_mood",
            "description": (
                "Discover movies matching a mood/vibe. "
                "Vibes: on-edge, slow-burn, dark, intense, feel-good, romantic, "
                "cosy, mind-bending, scary, funny, action-packed, tearjerker."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vibe": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["vibe"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending",
            "description": "Fetch trending movies or TV shows this week. Use as a freshness signal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "media_type": {"type": "string", "enum": ["movie", "tv"], "default": "movie"},
                    "window": {"type": "string", "enum": ["day", "week"], "default": "week"},
                    "limit": {"type": "integer", "default": 10},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_keyword",
            "description": "Find movies tagged with a keyword on TMDB (e.g. 'heist', 'revenge', 'psychological').",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_details",
            "description": "Get full details (runtime, genres, tagline) for a single TMDB movie ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_id": {"type": "integer"},
                },
                "required": ["movie_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_watch_providers",
            "description": (
                "Check streaming availability for a list of movie IDs in a country. "
                "Fires all lookups simultaneously. country: ISO 3166-1 alpha-2 (e.g. 'US', 'GB')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "movie_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Up to 10 TMDB movie IDs",
                    },
                    "country": {"type": "string", "default": "US"},
                },
                "required": ["movie_ids"],
            },
        },
    },
]

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Tonight's Pick — a conversational movie recommendation agent.

Your goal: given a user's mood and viewing context, find 3-4 streaming-ready movies
and present them grouped by vibe with a one-line "why this for you tonight" for each.

Rules:
- Keep tool calls focused. Resolve reference titles to IDs first, then use those IDs.
- Always call check_watch_providers on your final candidates (pass all IDs at once).
- Only recommend movies that are available on at least one streaming service.
- Group picks by sub-vibe (e.g. "If you want slow-burn tension → X", "For relentless edge → Y").
- Include runtime in your reply (get_movie_details if needed).
- Be concise — the final reply should be 4-8 lines, not an essay.
- Never recommend a movie the user has already rejected.
"""

# ---------------------------------------------------------------------------
# uAgent setup
# ---------------------------------------------------------------------------

agent = Agent(
    name="tonights-pick",
    seed=AGENT_SEED,
    port=AGENT_PORT,
    mailbox=True,  # enable Agentverse mailbox
)

fund_agent_if_low(agent.wallet.address())

chat_proto = Protocol("ChatProtocol")


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def _load_state(ctx: Context) -> dict:
    return {
        "vibe": ctx.storage.get("vibe") or "",
        "who": ctx.storage.get("who") or "",
        "reference": ctx.storage.get("reference") or "",
        "rejections": json.loads(ctx.storage.get("rejections") or "[]"),
        "history": json.loads(ctx.storage.get("history") or "[]"),
    }


def _save_state(ctx: Context, state: dict) -> None:
    ctx.storage.set("vibe", state["vibe"])
    ctx.storage.set("who", state["who"])
    ctx.storage.set("reference", state["reference"])
    ctx.storage.set("rejections", json.dumps(state["rejections"]))
    ctx.storage.set("history", json.dumps(state["history"]))


# ---------------------------------------------------------------------------
# Tool-use loop
# ---------------------------------------------------------------------------

async def run_tool_loop(messages: list[dict], rejections: list) -> str:
    """Call ASI1 with tool schemas; execute tool calls until a text reply is returned."""
    system_msg = {
        "role": "system",
        "content": SYSTEM_PROMPT
        + (
            f"\n\nAlready rejected movie IDs (do not recommend): {rejections}"
            if rejections
            else ""
        ),
    }
    loop_messages = [system_msg] + messages

    max_iterations = 8  # safety cap
    for _ in range(max_iterations):
        response = await asi1_client.chat.completions.create(
            model=ASI1_MODEL,
            messages=loop_messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        choice = response.choices[0]

        # If the model returned a text reply, we're done
        if choice.finish_reason == "stop" or choice.message.content:
            return choice.message.content or ""

        # Process tool calls
        tool_calls = choice.message.tool_calls or []
        if not tool_calls:
            return choice.message.content or ""

        # Add the assistant's tool-call message to history
        loop_messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls
            ],
        })

        # Execute each tool call and feed results back
        for tc in tool_calls:
            fn_name = tc.function.name
            fn_args = json.loads(tc.function.arguments)
            fn = TOOL_FUNCTIONS.get(fn_name)
            if fn is None:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})
            else:
                try:
                    result = await fn(**fn_args)
                except Exception as exc:
                    result = json.dumps({"error": str(exc)})

            loop_messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "Sorry, I ran into trouble finding good picks. Please try again."


# ---------------------------------------------------------------------------
# Intake checker
# ---------------------------------------------------------------------------

def _intake_complete(state: dict) -> bool:
    return bool(state["vibe"] and state["who"])


def _extract_intake(text: str, state: dict) -> dict:
    """Naively extract vibe/who/reference from raw user text.

    In production you'd run a small NER pass; here we do keyword matching.
    """
    lower = text.lower()

    # who
    if not state["who"]:
        if any(w in lower for w in ["partner", "girlfriend", "boyfriend", "wife", "husband", "date"]):
            state["who"] = "partner"
        elif any(w in lower for w in ["solo", "alone", "myself", "by myself"]):
            state["who"] = "solo"
        elif any(w in lower for w in ["family", "kids", "children"]):
            state["who"] = "family"
        elif any(w in lower for w in ["friend", "friends", "mates", "group"]):
            state["who"] = "friends"

    # vibe keywords
    if not state["vibe"]:
        vibe_keywords = [
            "on-edge", "slow-burn", "dark", "intense", "feel-good",
            "romantic", "cosy", "cozy", "mind-bending", "scary",
            "funny", "action-packed", "tearjerker", "thriller",
            "comedy", "horror", "drama",
        ]
        for kw in vibe_keywords:
            if kw in lower:
                state["vibe"] = kw
                break

    # reference movie (heuristic: "loved X", "like X", "watched X")
    if not state["reference"]:
        for trigger in ["loved ", "like ", "enjoyed ", "watched ", "similar to ", "fan of "]:
            idx = lower.find(trigger)
            if idx != -1:
                # grab up to 5 words after the trigger
                remainder = text[idx + len(trigger):]
                words = remainder.split()[:5]
                state["reference"] = " ".join(words).strip(".,!?")
                break

    return state


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------

from uagents import Model as UModel


class ChatMessage(UModel):
    session_id: str
    text: str


class ChatAcknowledgement(UModel):
    session_id: str
    status: str = "ok"


@chat_proto.on_message(model=ChatMessage, replies={ChatAcknowledgement})
async def on_chat_message(ctx: Context, sender: str, msg: ChatMessage) -> None:
    # Acknowledge immediately
    await ctx.send(sender, ChatAcknowledgement(session_id=msg.session_id))

    state = _load_state(ctx)

    # Append user turn to history
    state["history"].append({"role": "user", "content": msg.text})

    # Try to extract intake fields from this message
    state = _extract_intake(msg.text, state)

    if not _intake_complete(state):
        # Ask the one clarifying question
        follow_up = (
            "What's the vibe tonight — on-edge, slow-burn, dark, funny, romantic? "
            "And who are you watching with? Any movie you loved recently?"
        )
        state["history"].append({"role": "assistant", "content": follow_up})
        _save_state(ctx, state)
        reply_msg = ChatMessage(session_id=msg.session_id, text=follow_up)
        await ctx.send(sender, reply_msg)
        return

    # Intake complete — run the tool-use loop
    reply_text = await run_tool_loop(state["history"], state["rejections"])
    state["history"].append({"role": "assistant", "content": reply_text})
    _save_state(ctx, state)

    await ctx.send(sender, ChatMessage(session_id=msg.session_id, text=reply_text))


agent.include(chat_proto)

if __name__ == "__main__":
    agent.run()
