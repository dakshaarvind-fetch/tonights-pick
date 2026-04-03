"""FastMCP server entry point — used for local dev with Google ADK / Claude Desktop."""
from __future__ import annotations
from dotenv import load_dotenv

load_dotenv()

# Import mcp instance and all tool registrations
from .tools import mcp  # noqa: E402 — must come after load_dotenv


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
