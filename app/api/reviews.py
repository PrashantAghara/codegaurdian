import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.agents.supervisor import review_graph
from app.core.schemas import ReviewTriggerRequest
from app.domain.github.client import get_repo

logger = logging.getLogger("app.reviews")
router = APIRouter(prefix="/reviews", tags=["reviews"])


async def _run_review(repo_full_name: str, pr_number: int) -> None:
    try:
        repo = get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        result = await review_graph.ainvoke({"pr": pr, "repo": repo})
        logger.info(
            f"Manual review completed for {repo_full_name}#{pr_number}: {result.get('final_summary', '')[:200]}"
        )
    except Exception:
        logger.exception(f"Manual review failed for {repo_full_name}#{pr_number}")


@router.post("/trigger")
async def trigger_review(
    request: ReviewTriggerRequest, background_tasks: BackgroundTasks
):
    try:
        repo = get_repo(request.repo_full_name)
        repo.get_pull(request.pr_number)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"PR not found: {e}")

    background_tasks.add_task(_run_review, request.repo_full_name, request.pr_number)
    return {
        "status": "accepted",
        "repo": request.repo_full_name,
        "pr_number": request.pr_number,
    }
