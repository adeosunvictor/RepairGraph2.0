from pathlib import Path

from repairgraph.models import ReproductionResult
from repairgraph.sandbox.runner import SandboxRunner
from repairgraph.state import RepairGraphState
from repairgraph.tools.testing import run_pytest


def make_reproduction_node(runner: SandboxRunner):
    def reproduce(state: RepairGraphState) -> dict:
        result = run_pytest(runner, Path(state["repo_path"]))
        if result.infrastructure_error:
            reproduction = ReproductionResult(
                reproduced=False,
                infrastructure_error=True,
                evidence=(
                    "The configured sandbox could not execute the repository test suite. "
                    "This is an environment failure, not evidence of a software defect.\n"
                    f"{result.command_result.stderr[-4000:]}"
                ),
                command_result=result.command_result,
            )
            return {"reproduction": reproduction, "status": "environment_error"}

        reproduction = ReproductionResult(
            reproduced=not result.passed,
            evidence=(
                "Existing test suite fails before the repair; the failure is reproduction evidence."
                if not result.passed
                else "Existing test suite passes. No automatic reproduction was found."
            ),
            command_result=result.command_result,
            infrastructure_error=False,
        )
        return {
            "reproduction": reproduction,
            "status": "reproduced" if reproduction.reproduced else "not_reproduced",
        }

    return reproduce
