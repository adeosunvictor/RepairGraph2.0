from __future__ import annotations

import json
import time

from repairgraph.llm.provider import LLMProvider


class MockProvider(LLMProvider):
    """Deterministic provider for tests, CI, and orchestration evaluation."""

    def __init__(self) -> None:
        super().__init__()

    async def generate_text(self, system: str, user: str) -> str:
        started = time.perf_counter()
        self._add_stat("calls")
        text = (system + "\n" + user).lower()
        user_text = user.lower()
        request_text = user_text.split("json_schema:", 1)[0]
        try:
            if "triage" in text:
                intent = "diagnose" if any(
                    word in request_text for word in ("diagnose", "audit", "health check")
                ) else "repair"
                return json.dumps(
                    {
                        "type": "diagnostic" if intent == "diagnose" else "bug",
                        "severity": "P2",
                        "component": "booking-expiry",
                        "summary": "Investigate the reported repository behavior.",
                        "confidence": 0.95,
                        "intent": intent,
                    }
                )

            if "implementation plan" in text or "planner" in text:
                return json.dumps(
                    {
                        "hypothesis": "The failing behavior is localized to the relevant function.",
                        "steps": [
                            {
                                "order": 1,
                                "action": "Inspect the failing implementation and test",
                                "target": "relevant source and tests",
                                "expected_evidence": "failing assertion",
                            },
                            {
                                "order": 2,
                                "action": "Apply the smallest repair",
                                "target": "relevant source",
                                "expected_evidence": "passing regression test",
                            },
                        ],
                        "risk_notes": ["Preserve existing behavior outside the failing case"],
                    }
                )

            if "diagnosis agent" in text:
                return json.dumps(
                    {
                        "overall_status": "healthy",
                        "summary": "No reproducible defect was found by the existing test suite.",
                        "findings": [],
                        "recommended_improvements": [
                            "Keep the regression suite current and preserve test isolation."
                        ],
                        "files_reviewed": [],
                        "test_summary": "Existing test suite passed.",
                    }
                )

            if "independent reviewer" in text or "review the patch" in text:
                return json.dumps(
                    {
                        "approved": True,
                        "findings": [],
                        "rationale": "Patch is scoped and tests pass.",
                    }
                )

            if "security agent" in text or "independently assess" in text:
                return json.dumps(
                    {
                        "approved": True,
                        "findings": [],
                        "blocked_actions": [],
                        "risk_level": "low",
                    }
                )

            if "reflection agent" in text:
                return "Use the observed failure, keep the patch minimal, and preserve existing behavior."

            if "code agent" in text or "unified_diff" in text:
                if "booking" in text and "deadline" in text:
                    return json.dumps(
                        {
                            "unified_diff": (
                                "--- a/booking_expiry.py\n"
                                "+++ b/booking_expiry.py\n"
                                "@@ -1,6 +1,8 @@\n"
                                "-from datetime import datetime\n"
                                "+from datetime import datetime, timedelta\n"
                                " \n"
                                " \n"
                                " def request_deadline(created_at: datetime) -> datetime:\n"
                                "-    \"\"\"BUG: 09:00 is anchored to the same calendar day.\"\"\"\n"
                                "-    return created_at.replace(hour=9, minute=0, second=0, microsecond=0)\n"
                                "+    deadline = created_at.replace(hour=9, minute=0, second=0, microsecond=0)\n"
                                "+    if deadline <= created_at:\n"
                                "+        deadline += timedelta(days=1)\n"
                                "+    return deadline\n"
                            ),
                            "rationale": "Move a same-day 09:00 deadline to the next day when necessary.",
                            "files_changed": ["booking_expiry.py"],
                        }
                    )
                if "phone" in text and "normalize" in text:
                    return json.dumps(
                        {
                            "unified_diff": (
                                "--- a/phones.py\n"
                                "+++ b/phones.py\n"
                                "@@ -1,2 +1,5 @@\n"
                                " def normalize_phone(value: str) -> str:\n"
                                "+    value = value.replace(' ', '')\n"
                                "+    if value.startswith('0'):\n"
                                "+        return '+234' + value[1:]\n"
                                "     return value\n"
                            ),
                            "rationale": "Normalize local Nigerian numbers to international format.",
                            "files_changed": ["phones.py"],
                        }
                    )
                return json.dumps(
                    {
                        "unified_diff": "",
                        "rationale": "Mock provider has no fixture-specific repair.",
                        "files_changed": [],
                    }
                )

            return "{}"
        finally:
            self._add_stat("latency_seconds", time.perf_counter() - started)
