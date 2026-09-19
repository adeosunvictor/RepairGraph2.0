from __future__ import annotations

import subprocess
from pathlib import Path


def _run_git(
    repo: Path,
    args: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )


def _untracked_files(repo: Path) -> list[str]:
    result = _run_git(repo, ["ls-files", "--others", "--exclude-standard"])
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_diff(repo: Path) -> str:
    parts = [_run_git(repo, ["diff", "--no-ext-diff"]).stdout]
    for relative_path in _untracked_files(repo):
        result = _run_git(
            repo,
            ["diff", "--no-index", "--", "/dev/null", relative_path],
        )
        # git diff --no-index returns 1 when files differ, which is expected.
        if result.stdout:
            parts.append(result.stdout)
    return "\n".join(part for part in parts if part)


def git_changed_files(repo: Path) -> list[str]:
    tracked = _run_git(repo, ["diff", "--name-only"]).stdout.splitlines()
    files = [line.strip() for line in tracked if line.strip()]
    files.extend(_untracked_files(repo))
    return list(dict.fromkeys(files))


def apply_patch(repo: Path, unified_diff: str) -> tuple[bool, str]:
    if not unified_diff.strip():
        return False, "Empty patch"
    check = _run_git(
        repo,
        ["apply", "--check", "--whitespace=nowarn", "-"],
        input_text=unified_diff,
    )
    if check.returncode != 0:
        return False, check.stderr.strip() or "git apply --check rejected the patch"
    result = _run_git(
        repo,
        ["apply", "--whitespace=nowarn", "-"],
        input_text=unified_diff,
    )
    if result.returncode != 0:
        return False, result.stderr.strip() or "git apply failed"
    return True, "Patch applied"
