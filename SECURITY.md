# RepairGraph 2.0 Security

RepairGraph operates on untrusted repositories and must assume repository text can contain prompt injection, malicious code, unsafe paths, and dependency traps.

## Implemented controls

- isolated workspaces
- `.env` and secret-bearing local paths excluded from workspace copies
- workspace path containment
- repository search refuses workspace escapes
- allowlisted test/process commands
- Docker sandbox support with network disabled by default
- finite agent-step and repair-attempt budgets
- Git patch validation with `git apply --check`
- actual Git changed-file enumeration
- untracked/new file inclusion in diff/security review
- secret scanning
- protected path scanning
- CI workflow modification blocking
- independent reviewer and security gates
- no automatic merge

## Trust modes

`SANDBOX_BACKEND=docker` is the secure default for untrusted targets.

`--sandbox local` should only be used for repositories you trust and is useful when the target project's dependencies already exist in your local virtual environment.

## Known operational boundary

RepairGraph does not automatically install arbitrary target-repository dependencies into a sandbox. Automatically executing dependency installation from an untrusted repository would introduce supply-chain risk. If the sandbox lacks required dependencies, RepairGraph reports an environment error rather than falsely claiming it reproduced the bug.
