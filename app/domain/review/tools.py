import json
import os
import subprocess
import tempfile
from pathlib import Path

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
        encoding="utf-8",
        errors="replace",
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


def get_static_analysis_findings(pr, repo, filename: str) -> dict:
    """Run ruff for one file, scoped to changed lines. Python-only by design."""
    file_obj = next(f for f in pr.get_files() if f.filename == filename)
    full_content = get_full_file_content(pr, repo, filename)
    raw = _run_ruff_on_file(full_content)
    ranges = get_changed_line_ranges(file_obj.patch)
    return {"filename": filename, "findings": _filter_ruff_to_diff(raw, ranges)}


def make_static_analysis_tool(pr, repo):
    @tool
    def static_analysis_tool(filename: str) -> dict:
        """Run ruff against this PR's version of a file, scoped to only the changed lines."""
        return get_static_analysis_findings(pr, repo, filename)

    return static_analysis_tool


def _run_semgrep_on_file(full_content: str, filename: str) -> list[dict]:
    """Run Semgrep on one file. Preserving the real extension lets Semgrep auto-detect
    the language, so this works across Python, JS/TS, Java, Go, etc. without per-language code."""
    suffix = Path(filename).suffix or ".txt"
    with tempfile.NamedTemporaryFile(
        suffix=suffix, delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        tmp.write(full_content)
        tmp_path = tmp.name
    result = subprocess.run(
        ["semgrep", "--config=p/security-audit", "--json", tmp_path],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    os.unlink(tmp_path)
    try:
        data = json.loads(result.stdout)
        return data.get("results", [])
    except json.JSONDecodeError:
        return []


def _filter_semgrep_to_diff(
    findings: list[dict], ranges: list[tuple[int, int]]
) -> list[dict]:
    return [f for f in findings if any(s <= f["start"]["line"] <= e for s, e in ranges)]


def get_security_analysis_findings(pr, repo, filename: str) -> dict:
    """Run Semgrep for one file, scoped to changed lines. Multi-language — works on any file type
    Semgrep supports (30+ languages), unlike the old bandit-based version which was Python-only."""
    file_obj = next(f for f in pr.get_files() if f.filename == filename)
    full_content = get_full_file_content(pr, repo, filename)
    raw = _run_semgrep_on_file(full_content, filename)
    ranges = get_changed_line_ranges(file_obj.patch)
    filtered = _filter_semgrep_to_diff(raw, ranges)
    return {
        "filename": filename,
        "findings": [
            {
                "line": f["start"]["line"],
                "issue": f["extra"]["message"],
                "severity": f["extra"]["severity"],  # ERROR / WARNING / INFO
                "check_id": f["check_id"],
            }
            for f in filtered
        ],
    }


def make_security_analysis_tool(pr, repo):
    @tool
    def security_analysis_tool(filename: str) -> dict:
        """Run Semgrep against this PR's version of a file, scoped to only the changed lines,
        to find security issues. Works across multiple languages, not just Python."""
        return get_security_analysis_findings(pr, repo, filename)

    return security_analysis_tool
