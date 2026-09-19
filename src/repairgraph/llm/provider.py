from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    structured_output_attempts = 3

    def __init__(self) -> None:
        self._stats: dict[str, float | int] = {
            "calls": 0,
            "provider_retries": 0,
            "structured_retries": 0,
            "latency_seconds": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def _ensure_stats(self) -> None:
        if not hasattr(self, "_stats"):
            LLMProvider.__init__(self)

    def stats(self) -> dict[str, float | int]:
        self._ensure_stats()
        result = dict(self._stats)
        calls = int(result["calls"])
        result["mean_call_latency_seconds"] = (
            float(result["latency_seconds"]) / calls if calls else 0.0
        )
        return result

    def _add_stat(self, key: str, value: float | int = 1) -> None:
        self._ensure_stats()
        self._stats[key] = self._stats.get(key, 0) + value

    @abstractmethod
    async def generate_text(self, system: str, user: str) -> str:
        raise NotImplementedError

    async def close(self) -> None:
        """Release provider resources. Providers without resources may no-op."""
        return None

    async def generate_structured(
        self,
        system: str,
        user: str,
        schema: type[T],
    ) -> T:
        """Generate schema-valid JSON and repair malformed output when possible."""
        schema_json = json.dumps(schema.model_json_schema(), separators=(",", ":"))
        base_prompt = (
            f"{user}\n\n"
            "Return ONLY one valid JSON object matching the JSON Schema. "
            "Include every required field. Do not use markdown fences.\n"
            f"JSON_SCHEMA:{schema_json}"
        )
        prompt = base_prompt
        last_error: Exception | None = None
        last_raw = ""

        for attempt in range(1, self.structured_output_attempts + 1):
            raw = await self.generate_text(system, prompt)
            last_raw = raw
            try:
                data = self._extract_json(raw)
                return schema.model_validate(data)
            except (ValueError, json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt == self.structured_output_attempts:
                    break
                self._add_stat("structured_retries")
                previous = raw[-6000:]
                prompt = (
                    f"{base_prompt}\n\n"
                    "The previous response was invalid. Correct ONLY the structural/schema "
                    "problems and return a complete JSON object.\n"
                    f"VALIDATION_ERROR:{str(exc)[:2500]}\n"
                    f"PREVIOUS_RESPONSE:{previous}"
                )

        raise RuntimeError(
            "LLM could not produce valid structured output after "
            f"{self.structured_output_attempts} attempts. "
            f"Last error: {last_error}. Last response: {last_raw[:1000]}"
        ) from last_error

    @staticmethod
    def _extract_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise ValueError("Model did not return a JSON object") from exc
            value = json.loads(text[start : end + 1])
        if not isinstance(value, dict):
            raise ValueError("Model JSON response must be an object")
        return value
