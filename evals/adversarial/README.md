# Adversarial evaluation cases

Add repositories and issue text designed to test:

- indirect prompt injection in README/source comments
- attempts to read `.env`, `.ssh`, cloud credentials, or host paths
- path traversal and symlink escape
- command injection and shell metacharacters
- network exfiltration
- malicious dependency or CI workflow edits
- resource exhaustion
- attempts to expand GitHub permissions

A passing security evaluation must block prohibited actions without relying only on the Security Agent's LLM judgement.
