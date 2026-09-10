from langchain.agents import create_agent
from langchain_groq import ChatGroq

from app.core.config import settings
from app.domain.review.tools import make_security_analysis_tool

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)


def run_security_agent(pr, repo, filenames: list[str]) -> str:
    agent = create_agent(
        model=_llm,
        tools=[make_security_analysis_tool(pr, repo)],
        system_prompt=(
            "You are a Security Agent reviewing a pull request for security risks, using Semgrep, "
            "which works across multiple languages (Python, JS/TS, Java, Go, and more). "
            "Call security_analysis_tool once per given filename. "
            "Use the EXACT 'line' value from each finding — never estimate. "
            "Semgrep severities are ERROR, WARNING, or INFO — treat ERROR as high severity, "
            "WARNING as medium, INFO as low, when describing findings. "
            "Summarize findings grouped by severity, and end with a one-line verdict: PASS, PASS_WITH_WARNINGS, or FAIL. "
            "Any ERROR (high) severity finding should always result in FAIL, regardless of how few findings there are."
        ),
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Changed files: {filenames}"}]}
    )
    return result["messages"][-1].content
