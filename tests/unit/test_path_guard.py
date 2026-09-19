from pathlib import Path

import pytest

from repairgraph.security.path_guard import PathViolation, resolve_inside


def test_path_guard_allows_workspace_file(tmp_path: Path) -> None:
    assert resolve_inside(tmp_path, "src/app.py") == (tmp_path / "src/app.py").resolve()


def test_path_guard_blocks_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathViolation):
        resolve_inside(tmp_path, "../.env")
