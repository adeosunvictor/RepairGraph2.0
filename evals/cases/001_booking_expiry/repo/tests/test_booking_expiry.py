from datetime import datetime

from booking_expiry import request_deadline


def test_late_booking_deadline_is_future() -> None:
    created = datetime(2026, 9, 16, 22, 43)
    assert request_deadline(created) > created
