from __future__ import annotations

from pathlib import Path


class PathViolation(PermissionError):
    pass


def resolve_inside(root: Path, requested: str | Path) -> Path:
    root = root.resolve()
    candidate = (root / requested).resolve() if not Path(requested).is_absolute() else Path(requested).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathViolation(f"Path escapes workspace: {requested}") from exc
    return candidate
