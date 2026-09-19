# RepairGraph 2.0

**Multi-agent software diagnosis and autonomous repair engineer**

RepairGraph takes a software issue or diagnostic request, creates an isolated working copy of the repository, gathers repository evidence, reproduces the reported failure, proposes the smallest supported patch, executes tests, reflects on failed attempts, performs independent review and security review, and produces a human-reviewable PR report.

RepairGraph 2.0 also handles the case where **nothing is broken**. A health-check or non-reproducible report ends in a diagnosis report instead of inventing a patch.

## Workflow

```text
Issue / diagnostic request
        |
        v
     Triage
        |
        v
Repository Intelligence
        |
        v
      Planner
        |
        v
   Reproduction
     /      \
    /        \
repair       diagnose / not reproduced
  |                    |
  v                    v
Coder              Diagnosis
  |                    |
  v                    END
Tester
  |
  +-- fail --> Reflection --> Coder
  |
  v
Reviewer
  |
  +-- reject -> Reflection --> Coder
  |
  v
Security
  |
  v
PR Report / optional draft PR
```

## What changed in 2.0

- Reliable GPT-OSS handling through Cloudflare Responses API with low reasoning effort, plus Chat Completions fallback.
- Adaptive provider retries and output-token budgets.
- Structured-output repair when an LLM returns incomplete JSON.
- Diagnosis path for healthy repositories and non-reproducible reports.
- Full graph-state preservation after failures. No more misleading all-null error reports.
- Explicit failing-stage reporting.
- End-to-end, per-stage, LLM-call, retry, and token telemetry.
- Git-compatible patch validation before application.
- Real Git diff and actual changed files are the source of truth for review/security.
- Untracked/new files are included in security review.
- UTF-8-safe Git and subprocess handling on Windows.
- Sandbox dependency failures are classified as environment failures, not software defects.
- Repository search blocks workspace escapes and provides representative context for generic diagnosis requests.
- Security rejection remains terminal when security is required.
- Deterministic repair and diagnosis evaluation cases.

## Core stack

- Python 3.11+
- LangGraph
- Pydantic v2
- FastAPI
- Cloudflare Workers AI
- optional Groq provider
- pytest
- Docker sandbox
- Git / GitHub

## Quick validation

Activate your existing environment, then:

```powershell
pytest
```

Expected RepairGraph 2.0 baseline:

```text
23 passed
```

### Confirm the configured AI provider

```powershell
python -c "import asyncio; from repairgraph.config import settings; from repairgraph.llm.factory import build_provider; p=build_provider(settings); print('Provider:', settings.llm_provider); print('Model:', settings.cloudflare_model); print(asyncio.run(p.generate_text('You are a software engineering agent.', 'Reply only with: AI OK'))); asyncio.run(p.close())"
```

### Run against a trusted real repository

For your own/trusted repository, use the local test environment if its dependencies already exist in your virtual environment:

```powershell
repairgraph `
  --repo "https://github.com/adeosunvictor/Leads-Generation-Agent-.git" `
  --sandbox local `
  --issue-id "LEADS-TEST-001" `
  --title "Diagnose the LeadRun persistence flow" `
  --body "Diagnose whether the LeadRun service layer and persistence model are consistent. If a genuine reproducible defect exists, make the smallest correct repair. If nothing is broken, do not change working code and return an evidence-backed diagnosis."
```

For untrusted repositories, keep the default Docker sandbox.

### Run evaluation

Deterministic orchestration baseline:

```powershell
python -m evals.run_evals --provider mock
```

Real Cloudflare benchmark:

```powershell
python -m evals.run_evals --provider cloudflare
```

The real-provider evaluation reports repair success, regression-free repair, reproduction success, diagnosis success, false-repair rate, relevant-file hit rate, agent-error rate, mean repair attempts, LLM calls, tokens, P50 latency, and P95 latency.

## Status meanings

| Status | Meaning |
| --- | --- |
| `ready_for_pr` | Reproduced, patched, tests passed, review passed, security passed |
| `diagnosis_complete` | Diagnostic request completed without unnecessary code changes |
| `not_reproduced` | Reported defect could not be reproduced, diagnosis returned |
| `environment_error` | Test environment failed, not evidence of a repository defect |
| `max_attempts_exhausted` | Repair budget was exhausted |
| `security_rejected` | Security gate rejected the patch |
| `agent_error` | A graph stage failed. `metadata.failing_stage` identifies the stage |
| `workspace_error` | Repository could not be cloned/copied |

## Telemetry

Every `RepairReport` includes metadata such as:

```json
{
  "total_latency_seconds": 12.42,
  "stage_latencies_seconds": {
    "triage": 1.1,
    "repository": 0.05,
    "planner": 1.5
  },
  "llm": {
    "calls": 5,
    "provider_retries": 0,
    "structured_retries": 0,
    "input_tokens": 0,
    "output_tokens": 0
  },
  "failing_stage": "coder"
}
```

`failing_stage` is present on agent errors.

## Safety model

- Target repository content is treated as untrusted data.
- Repairs occur in an isolated workspace, never the source checkout.
- `.env`, `.ssh`, and related secret-bearing paths are excluded from local workspace copies.
- Docker runtime networking is disabled by default.
- Commands are allowlisted.
- Path traversal is blocked.
- Actual Git changes, not LLM-reported filenames, drive security review.
- Secret patterns and protected paths are scanned deterministically before LLM security review.
- Security rejection cannot be reasoned away by Reflection.
- Draft PR creation is disabled by default and merge is never automatic.

## Evaluation baseline

The included deterministic baseline validates orchestration and control flow across two seeded repairs and one healthy diagnosis case:

- repair success: 2/2
- regression-free repair: 2/2
- reproduction success: 2/2
- diagnosis success: 1/1
- false repairs: 0/1
- relevant-file hit: 3/3
- agent errors: 0/3
- mean repair attempts: 1.0

These are **deterministic system-mechanics metrics**, not claims about the intelligence of the production LLM. Run the Cloudflare evaluator before publishing model-performance claims.

## Repository layout

```text
src/repairgraph/
  agents/
  llm/
  sandbox/
  security/
  tools/
  graph.py
  models.py
  service.py

tests/
evals/
docs/
```

## Portfolio positioning

RepairGraph 2.0 demonstrates agent orchestration, failure recovery, structured generation, software testing, repository intelligence, sandboxing, deterministic security controls, evaluation engineering, provider resilience, observability, and human-in-the-loop delivery.
