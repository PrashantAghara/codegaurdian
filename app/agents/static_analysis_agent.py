from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from app.core.config import settings
from app.domain.review.tools import make_static_analysis_tool

_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, api_key=settings.groq_api_key
)


def run_static_analysis_agent(pr, repo, py_filenames: list[str]) -> str:
    agent = create_react_agent(
        model=_llm,
        tools=[make_static_analysis_tool(pr, repo)],
        prompt=(
            "You are a Static Analysis Agent reviewing a pull request. "
            "Call static_analysis_tool once per given filename. "
            "When summarizing, use the EXACT 'location.row' value as the Line number — never estimate. "
            "Summarize findings grouped by severity, end with a one-line verdict: PASS, PASS_WITH_WARNINGS, or FAIL."
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
