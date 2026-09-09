import json
import re

from langchain_groq import ChatGroq

from app.core.config import settings
from app.domain.github.client import get_changed_line_ranges
from app.domain.review.tools import (
    get_security_analysis_findings,
    get_static_analysis_findings,
)

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)


def collect_static_findings(pr, repo, py_filenames: list[str]) -> list[dict]:
    findings = []
    for filename in py_filenames:
        result = get_static_analysis_findings(pr, repo, filename)
        for f in result["findings"]:
            findings.append(
                {
                    "filename": filename,
                    "line": f["location"]["row"],
                    "severity": f.get("severity", "error"),
                    "source": "static_analysis",
                    "message": f"{f['message']} ({f['code']})",
                }
            )
    return findings


def collect_security_findings(pr, repo, py_filenames: list[str]) -> list[dict]:
    findings = []
    for filename in py_filenames:
        result = get_security_analysis_findings(pr, repo, filename)
        for f in result["findings"]:
            findings.append(
                {
                    "filename": filename,
                    "line": f["line"],
                    "severity": f["severity"],
                    "source": "security",
                    "message": f"{f['issue']} ({f['test_id']})",
                }
            )
    return findings


_STYLE_EXTRACTION_PROMPT = """Extract every distinct finding from this style review report into a JSON array.
Each element must have exactly these keys: "filename", "line" (integer), "severity" (one of: info, warning, error), "message".
Use the exact line numbers as written in the report. If a finding spans a range, use the first line number.
Output ONLY the JSON array, no markdown fences, no commentary. If there are no findings, output [].

REPORT:
{report}
"""


def _valid_diff_ranges(pr, filename: str) -> list[tuple[int, int]]:
    file_obj = next((f for f in pr.get_files() if f.filename == filename), None)
    if not file_obj:
        return []
    return get_changed_line_ranges(file_obj.patch)


def collect_style_findings(pr, style_report_text: str) -> list[dict]:
    """Extract structured findings from the Style Agent's prose report, then drop any
    whose line number doesn't actually fall within the diff — GitHub rejects inline
    comments outside the diff, and the Style Agent's line numbers are LLM-estimated,
    not tool-verified like static analysis/security. Dropped findings are still
    covered in the main review body text, so nothing is lost, only de-duplicated
    away from the inline-comment rendering."""
    result = _llm.invoke(_STYLE_EXTRACTION_PROMPT.format(report=style_report_text))
    raw = re.sub(
        r"^```(json)?|```$", "", result.content.strip(), flags=re.MULTILINE
    ).strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    validated = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename", "")
        line = int(item.get("line", -1))
        ranges = _valid_diff_ranges(pr, filename)
        if any(s <= line <= e for s, e in ranges):
            validated.append(
                {
                    "filename": filename,
                    "line": line,
                    "severity": item.get("severity", "info"),
                    "source": "style",
                    "message": item.get("message", ""),
                }
            )
    return validated
