# Changelog

## 2.0.0

- added diagnosis mode for healthy/non-reproducible repositories
- added Cloudflare GPT-OSS Responses API path with low reasoning effort and fallback
- added adaptive LLM retry/token behavior and structured-output repair
- preserved partial graph state and failing-stage information on errors
- added per-stage and end-to-end latency telemetry
- added LLM call/retry/token telemetry
- made real Git state authoritative for review and security
- added untracked-file security coverage
- added Windows UTF-8 subprocess handling
- separated environment failures from reproduced software defects
- expanded deterministic evaluation cases
- expanded unit/security regression suite
