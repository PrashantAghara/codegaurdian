import re
from functools import lru_cache

from app.core.config import settings
from github import Auth, Github


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
