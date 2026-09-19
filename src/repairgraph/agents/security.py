from pathlib import Path

from repairgraph.llm.provider import LLMProvider
from repairgraph.models import SecurityResult
from repairgraph.security.scanner import scan_changed_paths, scan_text
from repairgraph.state import RepairGraphState
from repairgraph.tools.git import git_changed_files, git_diff

SYSTEM = """You are the Security Agent in RepairGraph 2.0.
Independently assess the REAL Git diff for secret exposure, command injection, path traversal, privilege expansion, unsafe network access, malicious dependency changes, prompt-injection effects, and excessive scope.
Never weaken safeguards to make a patch pass. Return structured data only."""


def make_security_node(provider: LLMProvider):
    async def security(state: RepairGraphState) -> dict:
        repo = Path(state["repo_path"])
        diff = git_diff(repo)
        paths = git_changed_files(repo)
        deterministic = scan_changed_paths(paths) + scan_text(diff)
        if deterministic:
            result = SecurityResult(
                approved=False,
                findings=deterministic,
                blocked_actions=deterministic,
                risk_level="high",
            )
            return {"security": result, "status": "security_rejected"}

        result = await provider.generate_structured(
            SYSTEM,
            (
                f"ISSUE:\n{state['issue'].title}\n\n"
                f"CHANGED FILES:\n{paths}\n\n"
                f"REAL PATCH DIFF:\n{diff[:24000]}"
            ),
            SecurityResult,
        )
        return {
            "security": result,
            "status": "security_approved" if result.approved else "security_rejected",
        }

    return security
