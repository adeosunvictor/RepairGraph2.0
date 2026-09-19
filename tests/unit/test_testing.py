from pathlib import Path

from repairgraph.models import CommandResult
from repairgraph.tools.testing import run_pytest


class FakeRunner:
    def __init__(self, result: CommandResult) -> None:
        self.result = result

    def run(self, workspace: Path, command: list[str]) -> CommandResult:
        return self.result


def test_missing_dependency_is_environment_error(tmp_path: Path) -> None:
    runner = FakeRunner(
        CommandResult(
            command=["python", "-m", "pytest", "-q"],
            returncode=2,
            stderr="ModuleNotFoundError: No module named 'example_dependency'",
        )
    )
    result = run_pytest(runner, tmp_path)  # type: ignore[arg-type]
    assert result.infrastructure_error is True
    assert result.passed is False


def test_assertion_failure_is_not_environment_error(tmp_path: Path) -> None:
    runner = FakeRunner(
        CommandResult(
            command=["python", "-m", "pytest", "-q"],
            returncode=1,
            stdout="FAILED tests/test_app.py::test_value - assert 1 == 2",
        )
    )
    result = run_pytest(runner, tmp_path)  # type: ignore[arg-type]
    assert result.infrastructure_error is False
    assert result.passed is False
