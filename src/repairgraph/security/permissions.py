from __future__ import annotations

from enum import StrEnum


class Capability(StrEnum):
    READ_REPO = "read_repo"
    SEARCH_REPO = "search_repo"
    WRITE_WORKSPACE = "write_workspace"
    RUN_TESTS = "run_tests"
    CREATE_BRANCH = "create_branch"
    CREATE_DRAFT_PR = "create_draft_pr"


AGENT_CAPABILITIES: dict[str, frozenset[Capability]] = {
    "triage": frozenset(),
    "repository": frozenset({Capability.READ_REPO, Capability.SEARCH_REPO}),
    "planner": frozenset({Capability.READ_REPO}),
    "reproduction": frozenset({Capability.READ_REPO, Capability.RUN_TESTS}),
    "coder": frozenset({Capability.READ_REPO, Capability.WRITE_WORKSPACE}),
    "reviewer": frozenset({Capability.READ_REPO}),
    "security": frozenset({Capability.READ_REPO}),
    "pr": frozenset({Capability.CREATE_BRANCH, Capability.CREATE_DRAFT_PR}),
}


def require(agent: str, capability: Capability) -> None:
    if capability not in AGENT_CAPABILITIES.get(agent, frozenset()):
        raise PermissionError(f"Agent '{agent}' lacks capability '{capability}'")
