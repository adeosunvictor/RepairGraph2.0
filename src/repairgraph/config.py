from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    llm_provider: Literal["mock", "cloudflare", "groq"] = "cloudflare"

    cloudflare_account_id: str = ""
    cloudflare_api_token: str = ""
    cloudflare_model: str = "@cf/openai/gpt-oss-20b"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"

    github_token: str = ""
    github_owner: str = ""
    github_repo: str = ""
    github_webhook_secret: str = ""

    max_repair_attempts: int = 5
    max_agent_steps: int = 35

    max_llm_retries: int = 3
    llm_max_tokens: int = 4096

    require_reproduction: bool = True
    require_test_pass: bool = True
    require_security_pass: bool = True

    auto_create_branch: bool = True
    auto_create_draft_pr: bool = False

    sandbox_backend: Literal["docker", "local"] = "docker"
    sandbox_image: str = "repairgraph-sandbox:latest"
    sandbox_timeout_seconds: int = 300
    sandbox_memory_mb: int = 2048
    sandbox_cpu_limit: float = 2.0
    sandbox_network_enabled: bool = False

    workspace_root: Path = Path(".repairgraph/workspaces")

    use_mock_llm: bool = False
    enable_tracing: bool = False


settings = Settings()