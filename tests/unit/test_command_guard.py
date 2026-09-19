import pytest

from repairgraph.security.command_guard import CommandPolicy, CommandViolation


def test_allows_pytest() -> None:
    CommandPolicy().validate(["python", "-m", "pytest", "-q"])


def test_blocks_curl() -> None:
    with pytest.raises(CommandViolation):
        CommandPolicy().validate(["curl", "https://example.com"])


def test_blocks_env_path() -> None:
    with pytest.raises(CommandViolation):
        CommandPolicy().validate(["python", ".env"])
