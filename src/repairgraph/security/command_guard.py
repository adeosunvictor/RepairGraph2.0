from __future__ import annotations

from dataclasses import dataclass


class CommandViolation(PermissionError):
    pass


@dataclass(frozen=True)
class CommandPolicy:
    allowed_executables: frozenset[str] = frozenset({"python", "python3", "pytest", "ruff", "mypy", "bandit", "git"})
    denied_tokens: frozenset[str] = frozenset({"rm", "sudo", "curl", "wget", "ssh", "scp", "nc", "powershell", "cmd.exe"})

    def validate(self, command: list[str]) -> None:
        if not command:
            raise CommandViolation("Empty command")
        executable = command[0].split("/")[-1].lower()
        if executable not in self.allowed_executables:
            raise CommandViolation(f"Executable not allowed: {executable}")
        lowered = {part.lower() for part in command}
        blocked = lowered.intersection(self.denied_tokens)
        if blocked:
            raise CommandViolation(f"Denied command token(s): {', '.join(sorted(blocked))}")
        if any(".env" in part.lower() or ".ssh" in part.lower() for part in command):
            raise CommandViolation("Secret-bearing paths are not accessible")
