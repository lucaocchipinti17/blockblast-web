import re


EMAIL_RE = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)


def normalize_email(email: str) -> str:
    """Normalize an email address for lookup and storage."""
    if not isinstance(email, str):
        return ""
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    """Return whether an email address has a valid basic format."""
    return bool(EMAIL_RE.fullmatch(email))


def is_valid_password(password: str) -> bool:
    """Return whether a password satisfies the current minimum policy."""
    if not isinstance(password, str):
        return False
    return len(password) >= 8
