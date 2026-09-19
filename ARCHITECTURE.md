# RepairGraph 2.0 Architecture

RepairGraph 2.0 is a stateful LangGraph workflow with distinct agent responsibilities and deterministic control gates.

## Agent responsibilities

- **Triage** classifies request type, severity, component, confidence, and repair-vs-diagnosis intent.
- **Repository Intelligence** localizes relevant source/test files without sending the whole repository to the model.
- **Planner** forms an evidence-driven hypothesis and plan.
- **Reproduction** runs the existing test suite and distinguishes a real failing test from sandbox/infrastructure failure.
- **Diagnosis** handles health checks and non-reproducible reports without changing working code.
- **Code** proposes a validated Git unified diff.
- **Test** runs regression validation after patch application.
- **Reflection** uses observable failure evidence to guide another patch attempt.
- **Reviewer** independently examines the real Git diff and test evidence.
- **Security** combines deterministic controls with an independent LLM review of the real diff.
- **PR** creates a structured human-review report and can optionally create a draft PR.

## Control invariants

1. A reported defect is not patched when reproduction is required and no defect is reproduced.
2. Environment failures are not counted as reproduced defects.
3. Failed patches never progress to testing.
4. Failed tests and rejected reviews can reflect/retry within a finite repair budget.
5. Security rejection is terminal when `REQUIRE_SECURITY_PASS=true`.
6. Real Git state is authoritative for changed files.
7. Source repositories are never modified directly.
8. Human review remains required before merge.

## Provider resilience

For Cloudflare GPT-OSS, RepairGraph prefers the Responses API and requests low reasoning effort. It falls back to Chat Completions when the Responses endpoint is unavailable. Provider retries and structured-output retries are separate from semantic repair attempts.
