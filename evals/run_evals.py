from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import statistics
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from repairgraph.config import Settings
from repairgraph.models import Issue
from repairgraph.service import repair


@dataclass
class Metrics:
    total: int = 0
    repair_cases: int = 0
    diagnosis_cases: int = 0
    reproduced: int = 0
    repaired: int = 0
    regression_free: int = 0
    diagnosed: int = 0
    false_repairs: int = 0
    security_approved: int = 0
    relevant_file_hits: int = 0
    attempts: int = 0
    agent_errors: int = 0
    environment_errors: int = 0
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    latencies: list[float] = field(default_factory=list)
    case_results: list[dict] = field(default_factory=list)

    def report(self) -> dict:
        repair_denominator = max(self.repair_cases, 1)
        diagnosis_denominator = max(self.diagnosis_cases, 1)
        latency_sorted = sorted(self.latencies)
        p50 = statistics.median(latency_sorted) if latency_sorted else 0.0
        if latency_sorted:
            p95_index = max(0, min(len(latency_sorted) - 1, round(0.95 * len(latency_sorted) + 0.5) - 1))
            p95 = latency_sorted[p95_index]
        else:
            p95 = 0.0
        base = asdict(self)
        base.pop("latencies", None)
        return {
            **base,
            "reproduction_rate": self.reproduced / repair_denominator,
            "repair_success_rate": self.repaired / repair_denominator,
            "regression_free_rate": self.regression_free / repair_denominator,
            "diagnosis_success_rate": self.diagnosed / diagnosis_denominator,
            "false_repair_rate": self.false_repairs / diagnosis_denominator,
            "relevant_file_hit_rate": self.relevant_file_hits / max(self.total, 1),
            "agent_error_rate": self.agent_errors / max(self.total, 1),
            "mean_attempts_per_repair_case": self.attempts / repair_denominator,
            "mean_llm_calls_per_case": self.llm_calls / max(self.total, 1),
            "p50_end_to_end_latency_seconds": round(p50, 4),
            "p95_end_to_end_latency_seconds": round(p95, 4),
        }


async def run(provider: str) -> dict:
    root = Path(__file__).parent / "cases"
    metrics = Metrics()

    for case in sorted(path for path in root.iterdir() if path.is_dir()):
        issue = Issue.model_validate_json((case / "issue.json").read_text(encoding="utf-8"))
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        expect_repair = bool(expected.get("expect_repair", True))

        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "repo"
            shutil.copytree(case / "repo", source)
            settings = Settings(
                llm_provider=provider,
                use_mock_llm=provider == "mock",
                sandbox_backend="local",
                workspace_root=Path(temp) / "workspaces",
                auto_create_draft_pr=False,
            )
            report = await repair(issue, str(source), settings)

        metrics.total += 1
        if expect_repair:
            metrics.repair_cases += 1
        else:
            metrics.diagnosis_cases += 1
        metrics.attempts += report.attempts
        metrics.reproduced += int(
            expect_repair and bool(report.reproduction and report.reproduction.reproduced)
        )
        repaired = bool(report.tests and report.tests.passed and report.status == "ready_for_pr")
        metrics.repaired += int(expect_repair and repaired)
        metrics.regression_free += int(expect_repair and repaired)
        diagnosed = report.status in {"diagnosis_complete", "not_reproduced"} and report.diagnosis is not None
        metrics.diagnosed += int((not expect_repair) and diagnosed)
        metrics.false_repairs += int((not expect_repair) and report.attempts > 0)
        metrics.security_approved += int(bool(report.security and report.security.approved))
        metrics.agent_errors += int(report.status == "agent_error")
        metrics.environment_errors += int(
            bool(report.reproduction and report.reproduction.infrastructure_error)
        )

        matches = set(report.metadata.get("repository_matches", []))
        expected_files = set(expected.get("relevant_files", []))
        metrics.relevant_file_hits += int(bool(matches.intersection(expected_files)))

        llm = report.metadata.get("llm", {})
        metrics.llm_calls += int(llm.get("calls", 0))
        metrics.input_tokens += int(llm.get("input_tokens", 0))
        metrics.output_tokens += int(llm.get("output_tokens", 0))
        metrics.latencies.append(float(report.metadata.get("total_latency_seconds", 0.0)))
        metrics.case_results.append(
            {
                "case": case.name,
                "status": report.status,
                "attempts": report.attempts,
                "reproduced": bool(report.reproduction and report.reproduction.reproduced),
                "tests_passed": bool(report.tests and report.tests.passed),
                "diagnosed": diagnosed,
                "latency_seconds": report.metadata.get("total_latency_seconds", 0.0),
                "llm_calls": llm.get("calls", 0),
            }
        )

    return metrics.report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RepairGraph 2.0 evaluation suite")
    parser.add_argument("--provider", choices=["mock", "cloudflare", "groq"], default="mock")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(run(args.provider)), indent=2))
