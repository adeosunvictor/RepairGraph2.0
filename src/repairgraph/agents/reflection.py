from repairgraph.llm.provider import LLMProvider
from repairgraph.state import RepairGraphState

SYSTEM = """You are the Reflection Agent in RepairGraph 2.0.
Diagnose why the attempted repair failed using only observable evidence.
Recommend one precise correction for the next code attempt.
Do not propose bypassing tests, validation, review, or security controls."""


def make_reflection_node(provider: LLMProvider):
    async def reflect(state: RepairGraphState) -> dict:
        status = state.get("status", "")
        if status == "patch_apply_failed":
            evidence = state.get("reflection", "The generated patch could not be applied.")
        elif status == "review_rejected" and state.get("review"):
            review = state["review"]
            evidence = f"Reviewer findings: {review.findings}\nRationale: {review.rationale}"
        elif state.get("tests"):
            tests = state["tests"]
            evidence = tests.command_result.stdout + "\n" + tests.command_result.stderr
        else:
            evidence = state.get("reflection", "No evidence available.")

        text = await provider.generate_text(
            SYSTEM,
            (
                f"FAILED REPAIR: {state['issue'].title}\n"
                f"ATTEMPT: {state.get('attempts', 0)}\n"
                f"FAILURE TYPE: {status}\n\nEVIDENCE:\n{evidence[-12000:]}"
            ),
        )
        return {"reflection": text, "status": "reflected"}

    return reflect
