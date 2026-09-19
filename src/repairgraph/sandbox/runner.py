from __future__ import annotations

import os
import subprocess
from pathlib import Path

from repairgraph.models import CommandResult
from repairgraph.security.command_guard import CommandPolicy


class SandboxRunner:
    def __init__(
        self,
        *,
        backend: str,
        image: str,
        timeout_seconds: int,
        memory_mb: int,
        cpu_limit: float,
        network_enabled: bool,
    ) -> None:
        self.backend = backend
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.memory_mb = memory_mb
        self.cpu_limit = cpu_limit
        self.network_enabled = network_enabled
        self.policy = CommandPolicy()

    def run(self, workspace: Path, command: list[str]) -> CommandResult:
        self.policy.validate(command)
        workspace = workspace.resolve()
        if self.backend == "local":
            return self._run_local(workspace, command)
        if self.backend == "docker":
            return self._run_docker(workspace, command)
        raise ValueError(f"Unsupported sandbox backend: {self.backend}")

    def _run_local(self, workspace: Path, command: list[str]) -> CommandResult:
        safe_env = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {
                "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE",
                "PYTHONPATH", "VIRTUAL_ENV",
            }
        }
        safe_env["PYTHONUTF8"] = "1"
        safe_env["PYTHONIOENCODING"] = "utf-8"
        try:
            proc = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                env=safe_env,
                check=False,
            )
            return CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                command=command,
                returncode=124,
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
                timed_out=True,
            )

    def _run_docker(self, workspace: Path, command: list[str]) -> CommandResult:
        docker_command = [
            "docker", "run", "--rm",
            "--memory", f"{self.memory_mb}m",
            "--cpus", str(self.cpu_limit),
            "--pids-limit", "256",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=256m",
            "-e", "PYTHONUTF8=1",
            "-e", "PYTHONIOENCODING=utf-8",
            "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
        ]
        if not self.network_enabled:
            docker_command += ["--network", "none"]
        docker_command += [self.image, *command]
        try:
            proc = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_seconds,
                check=False,
            )
            return CommandResult(
                command=command,
                returncode=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
            )
        except FileNotFoundError:
            return CommandResult(
                command=command,
                returncode=127,
                stderr=(
                    "Docker executable not found. Install Docker Desktop or use "
                    "SANDBOX_BACKEND=local only for a trusted repository."
                ),
            )
        except subprocess.TimeoutExpired as exc:
            return CommandResult(
                command=command,
                returncode=124,
                stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
                stderr=(exc.stderr or "") if isinstance(exc.stderr, str) else "",
                timed_out=True,
            )
