from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


def isoformat_utc(value: datetime) -> str:
    """Serialize a datetime as an ISO-8601 UTC timestamp."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
