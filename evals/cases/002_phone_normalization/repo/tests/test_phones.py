from phones import normalize_phone


def test_local_phone_is_normalized() -> None:
    assert normalize_phone("08012345678") == "+2348012345678"


def test_international_phone_is_preserved() -> None:
    assert normalize_phone("+2348012345678") == "+2348012345678"
