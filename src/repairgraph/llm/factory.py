from repairgraph.config import Settings
from repairgraph.llm.cloudflare import CloudflareProvider
from repairgraph.llm.groq import GroqProvider
from repairgraph.llm.mock import MockProvider
from repairgraph.llm.provider import LLMProvider


def build_provider(settings: Settings) -> LLMProvider:
    if settings.use_mock_llm or settings.llm_provider == "mock":
        return MockProvider()
    if settings.llm_provider == "cloudflare":
        if not settings.cloudflare_account_id or not settings.cloudflare_api_token:
            raise ValueError("Cloudflare provider requires CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN")
        return CloudflareProvider(
            account_id=settings.cloudflare_account_id,
            api_token=settings.cloudflare_api_token,
            model=settings.cloudflare_model,
            max_retries=settings.max_llm_retries,
            max_tokens=settings.llm_max_tokens,
        )
    if settings.llm_provider == "groq":
        if not settings.groq_api_key:
            raise ValueError("Groq provider requires GROQ_API_KEY")
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            max_retries=settings.max_llm_retries,
            max_tokens=settings.llm_max_tokens,
        )
    raise ValueError(f"Unsupported provider: {settings.llm_provider}")
