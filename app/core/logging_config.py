import logging

_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "hpack",
    "mcp",
    "mcp.client",
    "langchain",
    "langchain_mcp_adapters",
    "langsmith",
    "urllib3",
    "huggingface_hub",
    "sentence_transformers",
    "filelock",
    "github",
    "asyncio",
)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    logging.getLogger("app").setLevel(logging.INFO)
