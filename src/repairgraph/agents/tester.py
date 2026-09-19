from pathlib import Path

from repairgraph.sandbox.runner import SandboxRunner
from repairgraph.state import RepairGraphState
from repairgraph.tools.testing import run_pytest


def make_test_node(runner: SandboxRunner):
    def test(state: RepairGraphState) -> dict:
        result = run_pytest(runner, Path(state["repo_path"]))
        if result.infrastructure_error:
            status = "environment_error"
        else:
            status = "tests_passed" if result.passed else "tests_failed"
        return {"tests": result, "status": status}

    return test
