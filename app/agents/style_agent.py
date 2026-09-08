from langchain_groq import ChatGroq

from app.core.config import settings
from app.domain.github.client import get_pr_diff_text
from app.domain.rag.service import retrieve_style_context

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)

BASELINE_RULES = """
- All function signatures must have type hints on parameters and return values
- Public functions must have a docstring describing purpose, args, and return value
- Function and variable names must be descriptive, not abbreviated (e.g. `user_id` not `uid`)
- Avoid nesting conditionals more than 3 levels deep — prefer early returns
"""

_BASELINE_PROMPT = """You are reviewing a pull request diff against ONLY these baseline rules:
{baseline_rules}

Diff:
{diff}

For each violation: filename, line (from diff hunk header), comment, severity (info/warning).
If none, say so explicitly."""

_PROJECT_CONTEXT_PROMPT = """You are reviewing a pull request diff against ONLY the conventions evident in this project's actual codebase (retrieved below) — not general best practices.

Retrieved project context:
{retrieved_context}

Diff:
{diff}

Identify anything in the diff that deviates from patterns clearly shown in the retrieved context above.
For each: filename, line (from diff hunk header), comment, severity (info/warning).
If the context doesn't clearly support a finding, say so rather than guessing."""


def run_style_agent(pr, filenames: list[str]) -> str:
    diff_text = get_pr_diff_text(pr, filenames)
    retrieved_context = retrieve_style_context(diff_text)

    baseline_result = _llm.invoke(
        _BASELINE_PROMPT.format(baseline_rules=BASELINE_RULES, diff=diff_text)
    )
    context_result = _llm.invoke(
        _PROJECT_CONTEXT_PROMPT.format(
            retrieved_context=retrieved_context, diff=diff_text
        )
    )

    merge_prompt = f"""Combine these two independent review passes into one final report. Keep each finding's source labeled.

BASELINE PASS RESULTS:
{baseline_result.content}

PROJECT-CONTEXT PASS RESULTS:
{context_result.content}

Output a combined list of findings (deduplicated if any overlap), each labeled [baseline] or [project-context], then end with one overall verdict: PASS, PASS_WITH_WARNINGS, or FAIL."""

    return _llm.invoke(merge_prompt).content
