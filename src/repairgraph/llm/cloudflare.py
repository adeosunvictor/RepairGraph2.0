from repairgraph.llm.openai_compatible import OpenAICompatibleProvider


class CloudflareProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        *,
        account_id: str,
        api_token: str,
        model: str,
        max_retries: int = 3,
        max_tokens: int = 4096,
    ) -> None:
        super().__init__(
            api_key=api_token,
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
            model=model,
            max_retries=max_retries,
            max_tokens=max_tokens,
            prefer_responses_api="gpt-oss" in model.lower(),
        )
