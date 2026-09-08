import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = str(PROJECT_ROOT / "mcp_servers" / "github_mcp" / "server.py")

_client = MultiServerMCPClient(
    {
        "github": {
            "command": sys.executable,
            "args": [SERVER_SCRIPT],
            "transport": "stdio",
        }
    }
)


async def get_github_mcp_tools():
    return await _client.get_tools()
