import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP

from app.domain.github.client import get_repo

mcp = FastMCP("codeguardian-github")


@mcp.tool()
def get_pr_files(repo_full_name: str, pr_number: int) -> list[dict]:
    """Get the list of changed files in a pull request, with filename, status, and patch."""
    repo = get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    return [
        {"filename": f.filename, "status": f.status, "patch": f.patch}
        for f in pr.get_files()
    ]


@mcp.tool()
def get_file_content(repo_full_name: str, path: str, ref: str) -> str:
    """Get the full content of a file at a specific commit ref."""
    repo = get_repo(repo_full_name)
    return repo.get_contents(path, ref=ref).decoded_content.decode("utf-8")


@mcp.tool()
def post_pr_comment(repo_full_name: str, pr_number: int, body: str) -> dict:
    """Post a general comment on a pull request."""
    repo = get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    comment = pr.create_issue_comment(body)
    return {"comment_id": comment.id, "url": comment.html_url}


@mcp.tool()
def create_check_run(
    repo_full_name: str, head_sha: str, conclusion: str, title: str, summary: str
) -> dict:
    """Create a check run on a commit. conclusion must be one of: success, failure, neutral, action_required."""
    repo = get_repo(repo_full_name)
    check = repo.create_check_run(
        name="CodeGuardian Review",
        head_sha=head_sha,
        status="completed",
        conclusion=conclusion,
        output={"title": title, "summary": summary},
    )
    return {"check_run_id": check.id, "url": check.html_url}


if __name__ == "__main__":
    mcp.run(transport="stdio")
