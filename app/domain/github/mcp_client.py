from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings

_client = MultiServerMCPClient(
    {
        "github": {
            "url": settings.mcp_server_url,
            "transport": "streamable_http",
        }
    }
)


async def get_github_mcp_tools():
    return await _client.get_tools()
