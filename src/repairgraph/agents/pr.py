from __future__ import annotations

import subprocess
from pathlib import Path

from repairgraph.config import Settings
from repairgraph.models import PRReport
from repairgraph.state import RepairGraphState
from repairgraph.tools.github import GitHubClient
from repairgraph.tools.git import git_changed_files


def _git(repo: Path, args: list[str], timeout: int = 30) -> None:
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def make_pr_node(settings: Settings):
    async def create_pr(state: RepairGraphState) -> dict:
        patch = state.get("patch")
        reproduction = state.get("reproduction")
        tests = state.get("tests")
        review = state.get("review")
        security = state.get("security")
        repo = Path(state["repo_path"])
        changed_files = git_changed_files(repo)

        report = PRReport(
            title=f"Fix: {state['issue'].title}",
            summary=patch.rationale if patch else f"Automated repair for {state['issue'].title}",
            root_cause=state["plan"].hypothesis if state.get("plan") else "Root cause not available.",
            files_changed=changed_files,
            attempts=state.get("attempts", 0),
            reproduction_evidence=reproduction.evidence if reproduction else None,
            test_summary=tests.summary if tests else None,
            reviewer_approved=bool(review and review.approved),
            security_approved=bool(security and security.approved),
            security_risk_level=security.risk_level if security else None,
            human_review_required=True,
        )

        if not settings.auto_create_draft_pr:
            return {"status": "ready_for_pr", "pr_report": report}
        if not settings.auto_create_branch:
            return {"status": "ready_for_pr_branch_creation_disabled", "pr_report": report}
        if not all([settings.github_token, settings.github_owner, settings.github_repo]):
            return {"status": "ready_for_pr_missing_github_config", "pr_report": report}

        branch = f"repairgraph/issue-{state['issue'].id}"
        _git(repo, ["checkout", "-B", branch])
        _git(repo, ["add", "-A"])
        _git(
            repo,
            [
                "-c", "user.name=RepairGraph",
                "-c", "user.email=repairgraph@local",
                "commit", "-m", f"fix: {state['issue'].title}",
            ],
        )
        _git(
            repo,
            [
                "-c", f"http.extraHeader=Authorization: Bearer {settings.github_token}",
                "push", "-u", "origin", branch,
            ],
            timeout=120,
        )

        changed_md = "\n".join(f"- `{path}`" for path in changed_files) or "- None"
        body = f"""## RepairGraph 2.0 automated repair

### Issue
{state['issue'].title}

### Summary
{report.summary}

### Root cause
{report.root_cause}

### Files changed
{changed_md}

### Validation
- Bug reproduced: {bool(reproduction and reproduction.reproduced)}
- Tests: {report.test_summary}
- Reviewer approved: {report.reviewer_approved}
- Security approved: {report.security_approved}
- Security risk: {report.security_risk_level}
- Repair attempts: {report.attempts}

Human review is required before merge.
"""
        client = GitHubClient(settings.github_token)
        try:
            pr = await client.create_draft_pr(
                settings.github_owner,
                settings.github_repo,
                title=report.title,
                head=branch,
                base="main",
                body=body,
            )
        finally:
            await client.close()
        report = report.model_copy(update={"draft_pr_url": pr.get("html_url")})
        return {"status": "draft_pr_created", "pr_report": report}

    return create_pr
