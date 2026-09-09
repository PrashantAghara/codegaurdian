import json
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header

from app.agents.supervisor import review_graph
from app.api.deps import verify_github_signature
from app.domain.github.client import get_repo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_HANDLED_PR_ACTIONS = {"opened", "synchronize", "reopened"}
_REVIEW_COMMANDS = ("/review",)


async def _run_review(repo_full_name: str, pr_number: int) -> None:
    try:
        repo = get_repo(repo_full_name)
        pr = repo.get_pull(pr_number)
        result = await review_graph.ainvoke({"pr": pr, "repo": repo})
        logger.info(
            f"Review completed for {repo_full_name}#{pr_number}: {result.get('final_summary', '')[:200]}"
        )
    except Exception:
        logger.exception(f"Review failed for {repo_full_name}#{pr_number}")


def _is_review_command(comment_body: str) -> bool:
    normalized = comment_body.strip().lower()
    # require the command at the start of the comment — avoids accidental matches
    # inside CodeGuardian's own posted review summaries if this bot account ever
    # comments on its own PRs elsewhere
    return any(normalized.startswith(cmd) for cmd in _REVIEW_COMMANDS)


@router.post("/github")
async def github_webhook(
    background_tasks: BackgroundTasks,
    body: bytes = Depends(verify_github_signature),
    x_github_event: str = Header(default=None),
):
    payload = json.loads(body)

    # --- Trigger 1: automatic, on PR open/update ---
    if x_github_event == "pull_request":
        action = payload.get("action")
        if action not in _HANDLED_PR_ACTIONS:
            return {"status": "ignored", "reason": f"action '{action}' not handled"}

        repo_full_name = payload["repository"]["full_name"]
        pr_number = payload["pull_request"]["number"]
        background_tasks.add_task(_run_review, repo_full_name, pr_number)
        return {
            "status": "accepted",
            "trigger": "automatic",
            "repo": repo_full_name,
            "pr_number": pr_number,
        }

    # --- Trigger 2: on-demand, via a PR comment command ---
    if x_github_event == "issue_comment":
        if payload.get("action") != "created":
            return {"status": "ignored", "reason": "not a new comment"}

        # issue_comment fires for both issues and PRs — only PR comments have this key
        if "pull_request" not in payload.get("issue", {}):
            return {"status": "ignored", "reason": "comment is not on a pull request"}

        comment_body = payload["comment"]["body"]
        if not _is_review_command(comment_body):
            return {
                "status": "ignored",
                "reason": "comment did not contain a review command",
            }

        repo_full_name = payload["repository"]["full_name"]
        pr_number = payload["issue"]["number"]
        background_tasks.add_task(_run_review, repo_full_name, pr_number)
        return {
            "status": "accepted",
            "trigger": "on_demand",
            "repo": repo_full_name,
            "pr_number": pr_number,
        }

    return {"status": "ignored", "reason": f"event type '{x_github_event}' not handled"}
