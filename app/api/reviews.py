from fastapi import APIRouter, HTTPException

from app.agents.supervisor import review_graph
from app.core.schemas import ReviewTriggerRequest, ReviewTriggerResponse
from app.domain.github.client import get_repo

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/trigger", response_model=ReviewTriggerResponse)
async def trigger_review(request: ReviewTriggerRequest):
    try:
        repo = get_repo(request.repo_full_name)
        pr = repo.get_pull(request.pr_number)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"PR not found: {e}")

    result = await review_graph.ainvoke({"pr": pr, "repo": repo})

    return ReviewTriggerResponse(
        final_summary=result.get("final_summary", ""),
        publish_result=result.get("publish_result"),
    )
