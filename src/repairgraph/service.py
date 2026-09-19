from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from repairgraph.config import Settings
from repairgraph.graph import StageExecutionError, build_graph
from repairgraph.llm.factory import build_provider
from repairgraph.models import Issue, RepairReport
from repairgraph.tools.workspace import create_workspace


def _stage_latencies(events: list[dict[str, Any]]) -> dict[str, float]:
    result: dict[str, float] = {}
    for event in events:
        if event.get("type") == "stage_completed" and event.get("stage"):
            key = str(event["stage"])
            result[key] = result.get(key, 0.0) + float(event.get("latency_seconds", 0.0))
    return result


def _report_from_state(
    *,
    issue: Issue,
    state: dict[str, Any],
    workspace: Path | None,
    status: str,
    metadata: dict[str, Any],
) -> RepairReport:
    return RepairReport(
        issue=issue,
        triage=state.get("triage"),
        plan=state.get("plan"),
        reproduction=state.get("reproduction"),
        diagnosis=state.get("diagnosis"),
        patch=state.get("patch"),
        tests=state.get("tests"),
        review=state.get("review"),
        security=state.get("security"),
        pr_report=state.get("pr_report"),
        attempts=state.get("attempts", 0),
        status=status,
        workspace=workspace,
        metadata=metadata,
    )


async def repair(issue: Issue, repo_source: str, settings: Settings) -> RepairReport:
    run_started = time.perf_counter()
    workspace: Path | None = None

    try:
        clone_started = time.perf_counter()
        workspace = create_workspace(repo_source, settings.workspace_root)
        workspace_latency = time.perf_counter() - clone_started
    except Exception as exc:
        return RepairReport(
            issue=issue,
            status="workspace_error",
            workspace=None,
            metadata={
                "error_type": type(exc).__name__,
                "error": str(exc),
                "failing_stage": "workspace",
                "total_latency_seconds": round(time.perf_counter() - run_started, 6),
            },
        )

    initial_state: dict[str, Any] = {
        "issue": issue,
        "repo_path": str(workspace),
        "attempts": 0,
        "status": "started",
        "events": [],
    }
    last_state: dict[str, Any] = dict(initial_state)
    provider = None

    try:
        provider = build_provider(settings)
        graph = build_graph(provider, settings)
        async for state in graph.astream(
            initial_state,
            config={"recursion_limit": settings.max_agent_steps},
            stream_mode="values",
        ):
            last_state = state

        events = list(last_state.get("events", []))
        context = last_state.get("repository_context")
        metadata = {
            "version": "2.0.0",
            "workspace_latency_seconds": round(workspace_latency, 6),
            "total_latency_seconds": round(time.perf_counter() - run_started, 6),
            "stage_latencies_seconds": _stage_latencies(events),
            "llm": provider.stats(),
            "events": events,
            "repository_matches": [match.path for match in context.matches] if context else [],
            "files_scanned": context.files_scanned if context else 0,
        }
        report = _report_from_state(
            issue=issue,
            state=last_state,
            workspace=workspace,
            status=last_state.get("status", "finished"),
            metadata=metadata,
        )
        await provider.close()
        return report

    except Exception as exc:
        original = exc.original if isinstance(exc, StageExecutionError) else exc
        failing_stage = exc.stage if isinstance(exc, StageExecutionError) else "unknown"
        events = list(last_state.get("events", []))
        context = last_state.get("repository_context")
        metadata = {
            "version": "2.0.0",
            "error_type": type(original).__name__,
            "error": str(original),
            "failing_stage": failing_stage,
            "last_status": last_state.get("status", "started"),
            "workspace_latency_seconds": round(workspace_latency, 6),
            "total_latency_seconds": round(time.perf_counter() - run_started, 6),
            "stage_latencies_seconds": _stage_latencies(events),
            "llm": provider.stats() if provider else {},
            "events": events,
            "repository_matches": [match.path for match in context.matches] if context else [],
            "files_scanned": context.files_scanned if context else 0,
        }
        report = _report_from_state(
            issue=issue,
            state=last_state,
            workspace=workspace,
            status="agent_error",
            metadata=metadata,
        )
        if provider:
            try:
                await provider.close()
            except Exception:
                pass
        return report
