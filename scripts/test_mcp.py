import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.domain.github.mcp_client import get_github_mcp_tools


async def main():
    tools = await get_github_mcp_tools()
    for t in tools:
        print(t.name, "-", t.description)


if __name__ == "__main__":
    asyncio.run(main())
