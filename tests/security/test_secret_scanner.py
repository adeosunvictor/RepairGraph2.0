from repairgraph.security.scanner import scan_changed_paths, scan_text


def test_blocks_env_modification() -> None:
    assert scan_changed_paths([".env"])


def test_flags_github_token() -> None:
    assert scan_text("token=ghp_abcdefghijklmnopqrstuvwxyz123456")
