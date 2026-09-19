import hashlib
import hmac

from repairgraph.tools.github import verify_webhook_signature


def test_valid_webhook_signature() -> None:
    secret = "test-secret"
    body = b'{"hello":"world"}'
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(secret, body, signature)


def test_invalid_webhook_signature() -> None:
    assert not verify_webhook_signature("secret", b"body", "sha256=bad")
