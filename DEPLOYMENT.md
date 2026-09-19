# Deployment

## Local, full-capability deployment

Version 0.1 is designed to run fully on a developer laptop:

- FastAPI and LangGraph run locally
- Cloudflare or Groq provides inference
- Docker provides isolated code execution
- GitHub provides repository/issue/PR integration

No GPU is required.

## Public demo

The FastAPI control plane can be deployed to a normal container host. However, most low-cost PaaS products do not permit safe nested Docker execution. Do not run untrusted repair commands directly inside the API container.

For a public demo, use one of these patterns:

1. Keep execution local and expose only recorded evaluation/demo results publicly.
2. Move sandbox execution to a disposable external runner such as a dedicated CI job or sandbox service.
3. Deploy only the API/control plane until an external execution backend is configured.

This separation is deliberate. It prevents a cheap hosting shortcut from weakening the system's primary security boundary.
