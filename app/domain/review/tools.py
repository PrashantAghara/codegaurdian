import json
import os
import subprocess
import tempfile

from langchain_core.tools import tool

from app.domain.github.client import get_changed_line_ranges, get_full_file_content


def _run_ruff_on_file(full_content: str) -> list[dict]:
    with tempfile.NamedTemporaryFile(
        suffix=".py", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(full_content)
        tmp_path = tmp.name
    result = subprocess.run(
        ["ruff", "check", tmp_path, "--output-format=json"],
        check=False,
        capture_output=True,
        text=True,
    )
    os.unlink(tmp_path)
    try:
        return json.loads(result.stdout) if result.stdout else []
    except json.JSONDecodeError:
        return []


def _filter_ruff_to_diff(
    findings: list[dict], ranges: list[tuple[int, int]]
) -> list[dict]:
    return [
        f for f in findings if any(s <= f["location"]["row"] <= e for s, e in ranges)
    ]


def make_static_analysis_tool(pr, repo):
    """Factory: binds a specific PR/repo so the tool needs no global state — safe for concurrent requests."""

    @tool
    def static_analysis_tool(filename: str) -> dict:
        """Run ruff against this PR's version of a file, scoped to only the changed lines."""
        file_obj = next(f for f in pr.get_files() if f.filename == filename)
        full_content = get_full_file_content(pr, repo, filename)
        raw = _run_ruff_on_file(full_content)
        ranges = get_changed_line_ranges(file_obj.patch)
        return {"filename": filename, "findings": _filter_ruff_to_diff(raw, ranges)}

    return static_analysis_tool


def _run_bandit_on_file(full_content: str) -> list[dict]:
    with tempfile.NamedTemporaryFile(
        suffix=".py", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(full_content)
        tmp_path = tmp.name
    result = subprocess.run(
        ["bandit", "-f", "json", tmp_path], check=False, capture_output=True, text=True
    )
    os.unlink(tmp_path)
    try:
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        return []


def _filter_bandit_to_diff(
    findings: list[dict], ranges: list[tuple[int, int]]
) -> list[dict]:
    return [f for f in findings if any(s <= f["line_number"] <= e for s, e in ranges)]


def make_security_analysis_tool(pr, repo):
    @tool
    def security_analysis_tool(filename: str) -> dict:
        """Run bandit against this PR's version of a file, scoped to only the changed lines, to find security issues."""
        file_obj = next(f for f in pr.get_files() if f.filename == filename)
        full_content = get_full_file_content(pr, repo, filename)
        raw = _run_bandit_on_file(full_content)
        ranges = get_changed_line_ranges(file_obj.patch)
        filtered = _filter_bandit_to_diff(raw, ranges)
        return {
            "filename": filename,
            "findings": [
                {
                    "line": f["line_number"],
                    "issue": f["issue_text"],
                    "severity": f["issue_severity"],
                    "confidence": f["issue_confidence"],
                    "test_id": f["test_id"],
                }
                for f in filtered
            ],
        }

    return security_analysis_tool
