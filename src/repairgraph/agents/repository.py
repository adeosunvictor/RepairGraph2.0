from pathlib import Path

from repairgraph.state import RepairGraphState
from repairgraph.tools.repository import search_repository


def repository_node(state: RepairGraphState) -> dict:
    issue = state["issue"]
    query = f"{issue.title}\n{issue.body}\n{state.get('triage', '')}"
    context = search_repository(Path(state["repo_path"]), query)
    return {"repository_context": context, "status": "repository_researched"}
