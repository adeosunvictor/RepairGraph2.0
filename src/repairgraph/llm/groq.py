from repairgraph.llm.openai_compatible import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_retries: int = 3,
        max_tokens: int = 4096,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model=model,
            max_retries=max_retries,
            max_tokens=max_tokens,
            prefer_responses_api=False,
        )
