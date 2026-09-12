from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings


def _normalize_mcp_url(raw: str) -> str:
    url = raw
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"
    if not url.rstrip("/").endswith("/mcp"):
        url = url.rstrip("/") + "/mcp"
    return url


_client = MultiServerMCPClient(
    {
        "github": {
            "url": _normalize_mcp_url(settings.mcp_server_url),
            "transport": "streamable_http",
        }
    }
)


async def get_github_mcp_tools():
    return await _client.get_tools()
