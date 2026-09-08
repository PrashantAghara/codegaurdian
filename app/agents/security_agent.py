from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.domain.review.tools import make_security_analysis_tool

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)


def run_security_agent(pr, repo, py_filenames: list[str]) -> str:
    agent = create_react_agent(
        model=_llm,
        tools=[make_security_analysis_tool(pr, repo)],
        prompt=(
            "You are a Security Agent reviewing a pull request for security risks. "
            "Call security_analysis_tool once per given filename. "
            "Use the EXACT 'line' value from each finding — never estimate. "
            "Summarize findings grouped by severity, and end with a one-line verdict: PASS, PASS_WITH_WARNINGS, or FAIL. "
            "Any 'high' severity finding should always result in FAIL, regardless of how few findings there are."
        ),
    )
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": f"Changed Python files: {py_filenames}"}
            ]
        }
    )
    return result["messages"][-1].content
