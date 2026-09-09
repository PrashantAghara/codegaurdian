from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.security_agent import run_security_agent
from app.agents.static_analysis_agent import run_static_analysis_agent
from app.agents.style_agent import run_style_agent
from app.agents.summarizer_agent import run_summarizer
from app.domain.github.client import get_py_filenames
from app.domain.github.review_publisher import publish_review
from app.domain.review.findings import (
    collect_security_findings,
    collect_static_findings,
    collect_style_findings,
)


class ReviewState(TypedDict):
    pr: object
    repo: object
    pr_title: str
    pr_body: str
    py_filenames: list[str]
    static_result: str | None
    style_result: str | None
    security_result: str | None
    findings: list[dict] | None
    final_summary: str | None
    skip_reason: str | None
    publish_result: dict | None


def gather_context_node(state: ReviewState) -> ReviewState:
    pr = state["pr"]
    return {
        **state,
        "pr_title": pr.title,
        "pr_body": pr.body or "(no description provided)",
        "py_filenames": get_py_filenames(pr),
    }


def supervisor_node(state: ReviewState) -> ReviewState:
    if not state["py_filenames"]:
        return {
            **state,
            "skip_reason": "No Python files changed — nothing for CodeGuardian to review.",
        }
    return state


def route_after_supervisor(state: ReviewState) -> str:
    return "skip" if state.get("skip_reason") else "review"


def static_analysis_node(state: ReviewState) -> ReviewState:
    result = run_static_analysis_agent(
        state["pr"], state["repo"], state["py_filenames"]
    )
    return {**state, "static_result": result}


def style_node(state: ReviewState) -> ReviewState:
    result = run_style_agent(state["pr"], state["py_filenames"])
    return {**state, "style_result": result}


def security_node(state: ReviewState) -> ReviewState:
    result = run_security_agent(state["pr"], state["repo"], state["py_filenames"])
    return {**state, "security_result": result}


def collect_findings_node(state: ReviewState) -> ReviewState:
    findings = []
    findings += collect_static_findings(
        state["pr"], state["repo"], state["py_filenames"]
    )
    findings += collect_security_findings(
        state["pr"], state["repo"], state["py_filenames"]
    )
    findings += collect_style_findings(state["pr"], state["style_result"])
    return {**state, "findings": findings}


def summarizer_node(state: ReviewState) -> ReviewState:
    result = run_summarizer(
        pr_title=state["pr_title"],
        pr_body=state["pr_body"],
        static_result=state["static_result"],
        style_result=state["style_result"],
        security_result=state["security_result"],
    )
    return {**state, "final_summary": result}


def skip_node(state: ReviewState) -> ReviewState:
    return {**state, "final_summary": f"**Verdict: SKIPPED**\n\n{state['skip_reason']}"}


async def publish_node(state: ReviewState) -> ReviewState:
    pr = state["pr"]
    repo = state["repo"]
    result = await publish_review(
        repo_full_name=repo.full_name,
        pr_number=pr.number,
        head_sha=pr.head.sha,
        summary_text=state["final_summary"],
        findings=state.get("findings") or [],
    )
    return {**state, "publish_result": result}


def build_review_graph():
    graph_builder = StateGraph(ReviewState)

    graph_builder.add_node("gather_context", gather_context_node)
    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("static_analysis", static_analysis_node)
    graph_builder.add_node("style", style_node)
    graph_builder.add_node("security", security_node)
    graph_builder.add_node("collect_findings", collect_findings_node)
    graph_builder.add_node("summarizer", summarizer_node)
    graph_builder.add_node("skip", skip_node)
    graph_builder.add_node("publish", publish_node)

    graph_builder.set_entry_point("gather_context")
    graph_builder.add_edge("gather_context", "supervisor")

    graph_builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"review": "static_analysis", "skip": "skip"},
    )

    graph_builder.add_edge("static_analysis", "style")
    graph_builder.add_edge("style", "security")
    graph_builder.add_edge("security", "collect_findings")
    graph_builder.add_edge("collect_findings", "summarizer")

    graph_builder.add_edge("summarizer", "publish")
    graph_builder.add_edge("skip", "publish")
    graph_builder.add_edge("publish", END)

    return graph_builder.compile()


review_graph = build_review_graph()
