import subprocess
from pathlib import Path

from repairgraph.tools.git import git_changed_files, git_diff


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    (path / "tracked.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=RepairGraph",
            "-c",
            "user.email=repairgraph@local",
            "commit",
            "-m",
            "baseline",
        ],
        cwd=path,
        check=True,
        capture_output=True,
    )


def test_git_changed_files_includes_untracked_files(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "new_file.py").write_text("secret = False\n", encoding="utf-8")
    assert "new_file.py" in git_changed_files(tmp_path)
    assert "new_file.py" in git_diff(tmp_path)


def test_git_changed_files_includes_tracked_modifications(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "tracked.py").write_text("value = 2\n", encoding="utf-8")
    assert git_changed_files(tmp_path) == ["tracked.py"]
