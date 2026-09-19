from __future__ import annotations

import ast
import re
from pathlib import Path

from repairgraph.models import FileMatch, RepositoryContext
from repairgraph.security.path_guard import PathViolation, resolve_inside

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".repairgraph",
}
TEXT_SUFFIXES = {
    ".py", ".toml", ".md", ".yaml", ".yml", ".json", ".js", ".ts", ".tsx", ".jsx"
}


def _keywords(text: str) -> set[str]:
    stop = {
        "this", "that", "with", "from", "when", "where", "should", "could", "would",
        "there", "their", "into", "while", "about", "issue", "repository", "system",
    }
    return {
        word
        for word in re.findall(r"[A-Za-z_][A-Za-z0-9_-]{2,}", text.lower())
        if len(word) > 2 and word not in stop
    }


def search_repository(repo: Path, query: str, limit: int = 8) -> RepositoryContext:
    repo = repo.resolve()
    query_words = _keywords(query)
    matches: list[FileMatch] = []
    tests: list[str] = []
    files_scanned = 0
    fallback_files: list[tuple[str, str]] = []

    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel_parts = path.relative_to(repo).parts
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        # Never follow a symlink to content outside the workspace.
        try:
            safe_path = resolve_inside(repo, path)
        except PathViolation:
            continue
        if safe_path.is_symlink():
            continue
        rel = path.relative_to(repo).as_posix()
        if "test" in path.name.lower() or "tests" in rel_parts:
            tests.append(rel)
        try:
            text = safe_path.read_text(encoding="utf-8", errors="ignore")[:120_000]
        except OSError:
            continue
        files_scanned += 1
        if len(fallback_files) < 20:
            fallback_files.append((rel, text))
        lower_text = text.lower()
        lower_rel = rel.lower()
        content_hits = sum(1 for word in query_words if word in lower_text)
        path_hits = sum(1 for word in query_words if word in lower_rel)
        if content_hits == 0 and path_hits == 0:
            continue
        # Path/name matches are especially valuable for source localization.
        raw_score = content_hits + (2.5 * path_hits)
        score = raw_score / max(1, len(query_words))
        excerpt = _best_excerpt(text, query_words)
        reason = f"Matched {content_hits} content terms and {path_hits} path terms"
        matches.append(FileMatch(path=rel, score=score, reason=reason, excerpt=excerpt))

    matches.sort(key=lambda item: (-item.score, item.path))
    if not matches:
        for rel, text in fallback_files[:limit]:
            matches.append(
                FileMatch(
                    path=rel,
                    score=0.01,
                    reason="Included as a representative repository file for generic diagnosis",
                    excerpt="\n".join(text.splitlines()[:40])[:3500],
                )
            )
    return RepositoryContext(
        matches=matches[:limit],
        candidate_test_files=sorted(tests)[:30],
        repo_summary=(
            f"Scanned {files_scanned} text/code files for {len(query_words)} meaningful issue terms."
        ),
        files_scanned=files_scanned,
    )


def _best_excerpt(text: str, words: set[str]) -> str:
    lines = text.splitlines()
    best_index = 0
    best_hits = 0
    for index, line in enumerate(lines):
        hits = sum(1 for word in words if word in line.lower())
        if hits > best_hits:
            best_hits = hits
            best_index = index
    start = max(0, best_index - 4)
    end = min(len(lines), best_index + 12)
    return "\n".join(lines[start:end])[:3500]


def read_file(repo: Path, relative_path: str, max_chars: int = 20_000) -> str:
    path = resolve_inside(repo, relative_path)
    return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]


def python_symbols(repo: Path, relative_path: str) -> list[str]:
    path = resolve_inside(repo, relative_path)
    if path.suffix != ".py":
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
