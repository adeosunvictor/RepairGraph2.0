import json

import pytest

from repairgraph.llm.provider import LLMProvider
from repairgraph.models import PatchProposal


class RepairingProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    async def generate_text(
        self,
        system: str,
        user: str,
    ) -> str:
        self.calls += 1

        if self.calls == 1:
            return json.dumps(
                {
                    "unified_diff": (
                        "*** Begin Patch\n"
                        "*** Update File: app.py\n"
                        "-old\n"
                        "+new\n"
                        "*** End Patch"
                    )
                }
            )

        return json.dumps(
            {
                "unified_diff": (
                    "--- a/app.py\n"
                    "+++ b/app.py\n"
                    "@@ -1 +1 @@\n"
                    "-old\n"
                    "+new\n"
                ),
                "rationale": (
                    "Correct the defect."
                ),
                "files_changed": [
                    "app.py",
                ],
            }
        )


@pytest.mark.asyncio
async def test_structured_output_retries_invalid_patch_proposal() -> None:
    provider = RepairingProvider()

    result = await provider.generate_structured(
        "coder",
        "Generate a patch",
        PatchProposal,
    )

    assert provider.calls == 2

    assert (
        result.rationale
        == "Correct the defect."
    )

    assert result.files_changed == [
        "app.py",
    ]

    assert result.unified_diff.startswith(
        "--- a/app.py"
    )


def test_patch_proposal_rejects_begin_patch_format() -> None:
    with pytest.raises(ValueError):
        PatchProposal(
            unified_diff=(
                "*** Begin Patch\n"
                "*** End Patch"
            ),
            rationale="Bad format",
            files_changed=[
                "app.py",
            ],
        )


def test_patch_proposal_allows_empty_diff_for_mock_failure_path() -> None:
    proposal = PatchProposal(
        unified_diff="",
        rationale=(
            "Mock provider emits no code change."
        ),
        files_changed=[],
    )

    assert proposal.unified_diff == ""