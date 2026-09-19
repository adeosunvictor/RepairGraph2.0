from pathlib import Path

from repairgraph.models import TestResult
from repairgraph.sandbox.runner import SandboxRunner

_INFRA_MARKERS = (
    "docker executable not found",
    "no module named",
    "modulenotfounderror",
    "cannot import name",
    "failed to import",
    "command not found",
    "is not recognized as an internal or external command",
)


def _is_infrastructure_failure(returncode: int, stdout: str, stderr: str) -> bool:
    if returncode == 127:
        return True
    combined = f"{stdout}\n{stderr}".lower()
    return any(marker in combined for marker in _INFRA_MARKERS)


def run_pytest(runner: SandboxRunner, repo: Path) -> TestResult:
    result = runner.run(repo, ["python", "-m", "pytest", "-q"])
    infrastructure_error = _is_infrastructure_failure(
        result.returncode, result.stdout, result.stderr
    )
    if result.returncode == 0:
        summary = "Test suite passed"
    elif infrastructure_error:
        summary = "Test environment failed before the repository could be evaluated"
    elif result.timed_out:
        summary = "Test suite timed out"
    else:
        summary = "Test suite failed"
    return TestResult(
        passed=result.returncode == 0,
        command_result=result,
        summary=summary,
        infrastructure_error=infrastructure_error,
    )
