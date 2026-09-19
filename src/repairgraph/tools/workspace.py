from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path


def _run(command: list[str], *, cwd: Path | None = None, timeout: int = 120) -> None:
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
    )


def create_workspace(source: str, workspace_root: Path) -> Path:
    workspace_root.mkdir(parents=True, exist_ok=True)
    destination = workspace_root / f"job-{uuid.uuid4().hex[:12]}"
    source_path = Path(source)

    if source_path.exists():
        shutil.copytree(
            source_path,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(
                ".venv", "venv", "__pycache__", ".repairgraph", ".pytest_cache",
                ".mypy_cache", ".ruff_cache", ".env", ".env.*", ".ssh",
            ),
        )
    elif source.startswith("https://") or source.startswith("git@"):
        _run(["git", "clone", "--depth", "1", source, str(destination)], timeout=120)
    else:
        raise FileNotFoundError(f"Repository source not found: {source}")

    if not (destination / ".git").exists():
        _run(["git", "init"], cwd=destination)
        _run(["git", "add", "."], cwd=destination)
        _run(
            [
                "git", "-c", "user.name=RepairGraph", "-c",
                "user.email=repairgraph@local", "commit", "-m", "baseline",
            ],
            cwd=destination,
        )
    return destination
