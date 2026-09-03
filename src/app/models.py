from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class User:
    """Represent a registered application user."""

    id: str
    email: str
    password_hash: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Session:
    """Represent a login session for one user on one client."""

    user_id: str
    token_hash: str
    created_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None
