import re
from functools import lru_cache

from app.core.config import settings
from github import Auth, Github, GithubIntegration

_app_private_key_cache = None


@lru_cache
def get_github_client() -> Github:
    return Github(auth=Auth.Token(settings.github_pat))


def get_repo(full_name: str):
    return get_github_client().get_repo(full_name)


def get_changed_line_ranges(patch: str) -> list[tuple[int, int]]:
    ranges = []
    for match in re.finditer(r"@@ -\d+,?\d* \+(\d+),?(\d*) @@", patch):
        start = int(match.group(1))
        length = int(match.group(2)) if match.group(2) else 1
        ranges.append((start, start + length - 1))
    return ranges


def get_pr_diff_text(pr, filenames: list[str]) -> str:
    diff_parts = []
    for f in pr.get_files():
        if f.filename in filenames:
            diff_parts.append(f"--- {f.filename} ---\n{f.patch}")
    return "\n\n".join(diff_parts)


def get_full_file_content(pr, repo, filename: str) -> str:
    return repo.get_contents(filename, ref=pr.head.sha).decoded_content.decode("utf-8")


def get_py_filenames(pr) -> list[str]:
    return [f.filename for f in pr.get_files() if f.filename.endswith(".py")]


def _get_app_private_key() -> str:
    global _app_private_key_cache
    if _app_private_key_cache is None:
        with open(settings.github_app_private_key_path, "r") as f:
            _app_private_key_cache = f.read()
    return _app_private_key_cache


def get_repo_as_app(full_name: str):
    """Return a Repository authenticated as the GitHub App installation — required for the Checks API."""
    owner, repo_name = full_name.split("/")
    integration = GithubIntegration(
        auth=Auth.AppAuth(settings.github_app_id, _get_app_private_key())
    )
    installation = integration.get_repo_installation(owner, repo_name)
    access_token = integration.get_access_token(installation.id).token
    app_client = Github(auth=Auth.Token(access_token))
    return app_client.get_repo(full_name)
