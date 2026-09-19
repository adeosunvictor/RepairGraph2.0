import pytest

from repairgraph.llm.mock import MockProvider
from repairgraph.models import TriageResult


@pytest.mark.asyncio
async def test_mock_provider_returns_valid_triage() -> None:
    result = await MockProvider().generate_structured("triage agent", "triage this issue", TriageResult)
    assert result.component == "booking-expiry"
    assert result.confidence > 0.9
