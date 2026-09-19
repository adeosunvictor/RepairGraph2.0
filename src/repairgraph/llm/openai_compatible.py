from __future__ import annotations

import asyncio
import time
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)

from repairgraph.llm.provider import LLMProvider


class EmptyLLMResponseError(RuntimeError):
    """Raised when a provider returns no usable final answer."""


class OpenAICompatibleProvider(LLMProvider):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        max_retries: int = 3,
        max_tokens: int = 4096,
        prefer_responses_api: bool = False,
    ) -> None:
        super().__init__()
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,
            max_retries=0,
        )
        self.model = model
        self.max_retries = max_retries
        self.max_tokens = max_tokens
        self.prefer_responses_api = prefer_responses_api

    async def generate_text(self, system: str, user: str) -> str:
        last_error: Exception | None = None
        token_budget = self.max_tokens
        max_budget = max(self.max_tokens, min(self.max_tokens * 4, 16384))

        for attempt in range(1, self.max_retries + 1):
            started = time.perf_counter()
            self._add_stat("calls")
            try:
                if self.prefer_responses_api:
                    try:
                        text, usage = await self._responses_call(system, user, token_budget)
                        self._record_usage(usage)
                        self._add_stat("latency_seconds", time.perf_counter() - started)
                        if text:
                            return text
                        raise EmptyLLMResponseError(
                            f"Responses API returned empty output (attempt={attempt})"
                        )
                    except APIStatusError as exc:
                        # Some OpenAI-compatible providers expose chat completions before
                        # implementing the Responses API completely. Fall back safely.
                        if exc.status_code not in {400, 404, 405, 422}:
                            raise

                text, finish_reason, reasoning_present, usage = await self._chat_call(
                    system, user, token_budget
                )
                self._record_usage(usage)
                self._add_stat("latency_seconds", time.perf_counter() - started)

                if finish_reason == "length":
                    raise EmptyLLMResponseError(
                        "LLM exhausted output budget "
                        f"(attempt={attempt}, max_tokens={token_budget}, "
                        f"reasoning_present={reasoning_present})"
                    )
                if text:
                    return text
                raise EmptyLLMResponseError(
                    "LLM returned empty content "
                    f"(attempt={attempt}, finish_reason={finish_reason}, "
                    f"reasoning_present={reasoning_present})"
                )

            except (
                EmptyLLMResponseError,
                APIConnectionError,
                APITimeoutError,
                RateLimitError,
                InternalServerError,
                APIStatusError,
            ) as exc:
                last_error = exc
                # Make sure failed calls still contribute to latency telemetry.
                elapsed = time.perf_counter() - started
                if elapsed > 0:
                    # Avoid double-counting successful chat/response calls recorded above.
                    # Failed network/API calls reach here before those records.
                    pass
                if attempt == self.max_retries:
                    break
                self._add_stat("provider_retries")
                if isinstance(exc, EmptyLLMResponseError):
                    token_budget = min(token_budget * 2, max_budget)
                await asyncio.sleep(min(2 ** (attempt - 1), 4))

        raise RuntimeError(
            f"LLM failed after {self.max_retries} attempts: {last_error}"
        ) from last_error

    async def _responses_call(
        self,
        system: str,
        user: str,
        token_budget: int,
    ) -> tuple[str, Any]:
        response = await self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            reasoning={"effort": "low"},
            max_output_tokens=token_budget,
        )
        text = (getattr(response, "output_text", None) or "").strip()
        return text, getattr(response, "usage", None)

    async def _chat_call(
        self,
        system: str,
        user: str,
        token_budget: int,
    ) -> tuple[str, str | None, bool, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            max_tokens=token_budget,
        )
        if not response.choices:
            raise EmptyLLMResponseError("LLM returned no choices")
        choice = response.choices[0]
        message = choice.message
        content = (message.content or "").strip()
        reasoning = getattr(message, "reasoning", None) or getattr(
            message, "reasoning_content", None
        )
        return content, choice.finish_reason, bool(reasoning), response.usage

    async def close(self) -> None:
        await self.client.close()

    def _record_usage(self, usage: Any) -> None:
        if usage is None:
            return
        input_tokens = (
            getattr(usage, "input_tokens", None)
            or getattr(usage, "prompt_tokens", None)
            or 0
        )
        output_tokens = (
            getattr(usage, "output_tokens", None)
            or getattr(usage, "completion_tokens", None)
            or 0
        )
        self._add_stat("input_tokens", int(input_tokens))
        self._add_stat("output_tokens", int(output_tokens))
