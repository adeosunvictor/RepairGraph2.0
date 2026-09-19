from pathlib import Path

from repairgraph.tools.repository import search_repository


def test_search_finds_relevant_file(tmp_path: Path) -> None:
    (tmp_path / "bookings.py").write_text("def calculate_expiry(created_at):\n    return created_at\n", encoding="utf-8")
    result = search_repository(tmp_path, "booking expiry created_at")
    assert result.matches
    assert result.matches[0].path == "bookings.py"
