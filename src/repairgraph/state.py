from __future__ import annotations

from typing import Any, TypedDict

from repairgraph.models import (
    DiagnosisReport,
    Issue,
    PatchProposal,
    PlanResult,
    PRReport,
    RepositoryContext,
    ReproductionResult,
    ReviewResult,
    SecurityResult,
    TestResult,
    TriageResult,
)


class RepairGraphState(TypedDict, total=False):
    issue: Issue
    repo_path: str
    triage: TriageResult
    repository_context: RepositoryContext
    plan: PlanResult
    reproduction: ReproductionResult
    diagnosis: DiagnosisReport
    patch: PatchProposal
    tests: TestResult
    review: ReviewResult
    security: SecurityResult
    attempts: int
    status: str
    reflection: str
    pr_report: PRReport
    events: list[dict[str, Any]]
