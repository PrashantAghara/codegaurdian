from app.domain.github.mcp_client import get_github_mcp_tools

_VERDICT_TO_CONCLUSION = {
    "APPROVE": "success",
    "REQUEST_CHANGES": "action_required",
    "ESCALATE": "failure",
    "SKIPPED": "neutral",
}


def extract_verdict(summary_text: str) -> str:
    for verdict in _VERDICT_TO_CONCLUSION:
        if verdict in summary_text:
            return verdict
    return "REQUEST_CHANGES"  # conservative default if parsing fails


async def publish_review(
    repo_full_name: str, pr_number: int, head_sha: str, summary_text: str
) -> dict:
    tools = await get_github_mcp_tools()
    post_comment_tool = next(t for t in tools if t.name == "post_pr_comment")
    create_check_tool = next(t for t in tools if t.name == "create_check_run")

    comment_result = await post_comment_tool.ainvoke(
        {
            "repo_full_name": repo_full_name,
            "pr_number": pr_number,
            "body": summary_text,
        }
    )

    verdict = extract_verdict(summary_text)
    conclusion = _VERDICT_TO_CONCLUSION[verdict]

    check_result = await create_check_tool.ainvoke(
        {
            "repo_full_name": repo_full_name,
            "head_sha": head_sha,
            "conclusion": conclusion,
            "title": f"CodeGuardian Review — {verdict}",
            "summary": summary_text,
        }
    )

    return {"comment": comment_result, "check_run": check_result}
