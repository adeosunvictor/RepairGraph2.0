from __future__ import annotations

import re
from pathlib import PurePosixPath

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?:api[_-]?key|token|secret)\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{16,}", re.I),
]
SENSITIVE_PATH_PARTS = {".env", ".ssh", ".aws", ".gnupg"}


def scan_text(text: str) -> list[str]:
    findings: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(f"Potential secret matched pattern: {pattern.pattern}")
    return findings


def scan_changed_paths(paths: list[str]) -> list[str]:
    findings: list[str] = []
    for raw in paths:
        normalized = raw.replace("\\", "/")
        path = PurePosixPath(normalized)
        lower_parts = {part.lower() for part in path.parts}
        if lower_parts.intersection(SENSITIVE_PATH_PARTS):
            findings.append(f"Sensitive path modified: {raw}")
        if normalized.lower().startswith(".github/workflows/"):
            findings.append(f"Workflow modification requires human approval: {raw}")
    return findings
