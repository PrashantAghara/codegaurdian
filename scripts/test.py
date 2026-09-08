import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.supervisor import review_graph
from app.domain.github.client import get_repo


async def main():
    repo = get_repo("PrashantAghara/fastapi")
    pr = next(
        p for p in repo.get_pulls(state="open") if p.head.ref == "test/lint-violation"
    )
    result = await review_graph.ainvoke({"pr": pr, "repo": repo})
    print(result["final_summary"])
    print("\n--- Publish result ---")
    print(result["publish_result"])


if __name__ == "__main__":
    asyncio.run(main())
