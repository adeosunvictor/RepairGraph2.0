from __future__ import annotations

import inspect
import time
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from repairgraph.agents.coder import make_coder_node
from repairgraph.agents.diagnosis import make_diagnosis_node
from repairgraph.agents.planner import make_planner_node
from repairgraph.agents.pr import make_pr_node
from repairgraph.agents.reflection import make_reflection_node
from repairgraph.agents.repository import repository_node
from repairgraph.agents.reproduction import make_reproduction_node
from repairgraph.agents.reviewer import make_reviewer_node
from repairgraph.agents.security import make_security_node
from repairgraph.agents.tester import make_test_node
from repairgraph.agents.triage import make_triage_node
from repairgraph.config import Settings
from repairgraph.llm.provider import LLMProvider
from repairgraph.sandbox.runner import SandboxRunner
from repairgraph.state import RepairGraphState


class StageExecutionError(RuntimeError):
    def __init__(self, stage: str, original: Exception) -> None:
        self.stage = stage
        self.original = original
        super().__init__(f"{stage} failed: {original}")


def _timed(stage: str, node: Callable[..., Any]):
    async def wrapped(state: RepairGraphState) -> dict:
        started = time.perf_counter()
        try:
            result = node(state)
            if inspect.isawaitable(result):
                result = await result
        except Exception as exc:
            raise StageExecutionError(stage, exc) from exc
        elapsed = time.perf_counter() - started
        events = list(result.get("events", state.get("events", [])))
        events.append(
            {
                "type": "stage_completed",
                "stage": stage,
                "latency_seconds": round(elapsed, 6),
                "status": result.get("status", state.get("status", "")),
            }
        )
        result["events"] = events
        return result

    return wrapped


def build_graph(provider: LLMProvider, settings: Settings):
    runner = SandboxRunner(
        backend=settings.sandbox_backend,
        image=settings.sandbox_image,
        timeout_seconds=settings.sandbox_timeout_seconds,
        memory_mb=settings.sandbox_memory_mb,
        cpu_limit=settings.sandbox_cpu_limit,
        network_enabled=settings.sandbox_network_enabled,
    )
    builder = StateGraph(RepairGraphState)

    def max_attempts_node(state: RepairGraphState) -> dict:
        return {"status": "max_attempts_exhausted"}

    def stop_node(state: RepairGraphState) -> dict:
        return {"status": state.get("status", "stopped")}

    nodes = {
        "triage": make_triage_node(provider),
        "repository": repository_node,
        "planner": make_planner_node(provider),
        "reproduction": make_reproduction_node(runner),
        "diagnosis": make_diagnosis_node(provider),
        "coder": make_coder_node(provider),
        "tester": make_test_node(runner),
        "reflection": make_reflection_node(provider),
        "reviewer": make_reviewer_node(provider),
        "security": make_security_node(provider),
        "pr": make_pr_node(settings),
        "max_attempts": max_attempts_node,
        "stop": stop_node,
    }
    for name, node in nodes.items():
        builder.add_node(name, _timed(name, node))

    builder.add_edge(START, "triage")
    builder.add_edge("triage", "repository")
    builder.add_edge("repository", "planner")
    builder.add_edge("planner", "reproduction")

    def after_reproduction(state: RepairGraphState) -> str:
        reproduction = state.get("reproduction")
        triage = state.get("triage")
        if reproduction and reproduction.infrastructure_error:
            return "diagnosis"
        if triage and triage.intent == "diagnose":
            return "diagnosis"
        if settings.require_reproduction and reproduction and not reproduction.reproduced:
            return "diagnosis"
        return "coder"

    builder.add_conditional_edges(
        "reproduction", after_reproduction, {"diagnosis": "diagnosis", "coder": "coder"}
    )
    builder.add_edge("diagnosis", END)

    def after_coder(state: RepairGraphState) -> str:
        if state.get("status") == "patch_apply_failed":
            return (
                "max_attempts"
                if state.get("attempts", 0) >= settings.max_repair_attempts
                else "reflection"
            )
        return "tester"

    builder.add_conditional_edges(
        "coder",
        after_coder,
        {"tester": "tester", "reflection": "reflection", "max_attempts": "max_attempts"},
    )

    def after_tests(state: RepairGraphState) -> str:
        tests = state.get("tests")
        if tests and tests.infrastructure_error:
            return "stop"
        if tests and tests.passed:
            return "reviewer"
        if not settings.require_test_pass:
            return "reviewer"
        return (
            "max_attempts"
            if state.get("attempts", 0) >= settings.max_repair_attempts
            else "reflection"
        )

    builder.add_conditional_edges(
        "tester",
        after_tests,
        {
            "reviewer": "reviewer",
            "reflection": "reflection",
            "max_attempts": "max_attempts",
            "stop": "stop",
        },
    )
    builder.add_edge("reflection", "coder")

    def after_review(state: RepairGraphState) -> str:
        review = state.get("review")
        if review and review.approved:
            return "security"
        return (
            "max_attempts"
            if state.get("attempts", 0) >= settings.max_repair_attempts
            else "reflection"
        )

    builder.add_conditional_edges(
        "reviewer",
        after_review,
        {"security": "security", "reflection": "reflection", "max_attempts": "max_attempts"},
    )

    def after_security(state: RepairGraphState) -> str:
        security = state.get("security")
        if security and security.approved:
            return "pr"
        return "stop" if settings.require_security_pass else "pr"

    builder.add_conditional_edges("security", after_security, {"pr": "pr", "stop": "stop"})
    builder.add_edge("pr", END)
    builder.add_edge("max_attempts", END)
    builder.add_edge("stop", END)
    return builder.compile()
