from langchain_mcp_adapters.client import MultiServerMCPClient

_client = MultiServerMCPClient(
    {
        "github": {
            "url": "http://127.0.0.1:8001/mcp",
            "transport": "streamable_http",
        }
    }
)


async def get_github_mcp_tools():
    return await _client.get_tools()
