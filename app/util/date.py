from datetime import datetime, timezone


def get_now() -> datetime:
    return datetime.now(timezone.utc)
