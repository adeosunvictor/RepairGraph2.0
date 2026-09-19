from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class IssueType(StrEnum):
    BUG = "bug"
    FEATURE = "feature"
    CI_FAILURE = "ci_failure"
    DEPENDENCY = "dependency"
    MAINTENANCE = "maintenance"
    DIAGNOSTIC = "diagnostic"
    OTHER = "other"


class Severity(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Issue(BaseModel):
    id: str
    title: str
    body: str = ""
    url: str | None = None
    labels: list[str] = Field(default_factory=list)


class TriageResult(BaseModel):
    type: IssueType
    severity: Severity
    component: str
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    intent: Literal["repair", "diagnose"] = "repair"


class FileMatch(BaseModel):
    path: str
    score: float = Field(ge=0)
    reason: str
    excerpt: str = ""


class RepositoryContext(BaseModel):
    matches: list[FileMatch] = Field(default_factory=list)
    candidate_test_files: list[str] = Field(default_factory=list)
    repo_summary: str = ""
    files_scanned: int = 0


class PlanStep(BaseModel):
    order: int
    action: str
    target: str | None = None
    expected_evidence: str | None = None


class PlanResult(BaseModel):
    hypothesis: str
    steps: list[PlanStep]
    risk_notes: list[str] = Field(default_factory=list)


class CommandResult(BaseModel):
    command: list[str]
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class ReproductionResult(BaseModel):
    reproduced: bool
    evidence: str
    command_result: CommandResult | None = None
    infrastructure_error: bool = False


class PatchProposal(BaseModel):
    unified_diff: str
    rationale: str
    files_changed: list[str] = Field(default_factory=list)

    @field_validator("unified_diff")
    @classmethod
    def require_git_unified_diff(cls, value: str) -> str:
        text = value.strip()
        if not text:
            return value
        if "*** Begin Patch" in text or "*** End Patch" in text:
            raise ValueError(
                "unified_diff must be a git-compatible unified diff, not Begin Patch format"
            )
        if "--- " not in text or "+++ " not in text or "@@" not in text:
            raise ValueError(
                "unified_diff must contain standard unified-diff headers and at least one hunk"
            )
        return value


class TestResult(BaseModel):
    passed: bool
    command_result: CommandResult
    summary: str
    infrastructure_error: bool = False


class ReviewResult(BaseModel):
    approved: bool
    findings: list[str] = Field(default_factory=list)
    rationale: str = ""


class SecurityResult(BaseModel):
    approved: bool
    findings: list[str] = Field(default_factory=list)
    blocked_actions: list[str] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high", "critical"] = "low"


class DiagnosisFinding(BaseModel):
    severity: Literal["info", "low", "medium", "high"] = "info"
    category: str
    file: str | None = None
    evidence: str
    recommendation: str


class DiagnosisReport(BaseModel):
    overall_status: Literal["healthy", "needs_attention", "not_reproduced"]
    summary: str
    findings: list[DiagnosisFinding] = Field(default_factory=list)
    recommended_improvements: list[str] = Field(default_factory=list)
    files_reviewed: list[str] = Field(default_factory=list)
    test_summary: str | None = None


class PRReport(BaseModel):
    title: str
    summary: str
    root_cause: str
    files_changed: list[str] = Field(default_factory=list)
    attempts: int = 0
    reproduction_evidence: str | None = None
    test_summary: str | None = None
    reviewer_approved: bool = False
    security_approved: bool = False
    security_risk_level: Literal["low", "medium", "high", "critical"] | None = None
    human_review_required: bool = True
    draft_pr_url: str | None = None


class RepairReport(BaseModel):
    issue: Issue
    triage: TriageResult | None = None
    plan: PlanResult | None = None
    reproduction: ReproductionResult | None = None
    diagnosis: DiagnosisReport | None = None
    patch: PatchProposal | None = None
    tests: TestResult | None = None
    review: ReviewResult | None = None
    security: SecurityResult | None = None
    attempts: int = 0
    status: str
    workspace: Path | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    pr_report: PRReport | None = None
