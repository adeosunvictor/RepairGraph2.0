# Threat Model Notes

Primary assets: source code, GitHub credentials, LLM keys, host filesystem, developer SSH keys, and pull-request integrity.

Primary adversaries: malicious repository authors, malicious issue authors, compromised dependencies, prompt-injection content, and faulty model output.

Primary design principle: model output is a proposal, never authority. Deterministic policy gates decide what can be read, executed, or published.
