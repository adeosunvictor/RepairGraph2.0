from datetime import datetime


def request_deadline(created_at: datetime) -> datetime:
    """BUG: 09:00 is anchored to the same calendar day."""
    return created_at.replace(hour=9, minute=0, second=0, microsecond=0)
