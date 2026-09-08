from langchain_groq import ChatGroq

from app.core.config import settings

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)

_SUMMARIZER_PROMPT = """You are a Summarizer Agent producing a final PR review from three independent agent reports.

PR TITLE: {pr_title}
PR DESCRIPTION: {pr_body}

STATIC ANALYSIS REPORT:
{static_analysis}

STYLE REPORT:
{style}

SECURITY REPORT:
{security}

Produce:
1. A concise PR summary (2-3 sentences) — note if the implementation appears to match the stated title/description
2. A suggested commit message (conventional-commits style)
3. Consolidated findings, grouped by severity
4. OVERALL VERDICT: APPROVE, REQUEST_CHANGES, or ESCALATE
   - ESCALATE only if the security report has any high-severity finding
   - REQUEST_CHANGES if there are any warnings/errors from static analysis or style
   - APPROVE only if all three reports are clean
"""


def run_summarizer(
    pr_title: str,
    pr_body: str,
    static_result: str,
    style_result: str,
    security_result: str,
) -> str:
    result = _llm.invoke(
        _SUMMARIZER_PROMPT.format(
            pr_title=pr_title,
            pr_body=pr_body,
            static_analysis=static_result,
            style=style_result,
            security=security_result,
        )
    )
    return result.content
