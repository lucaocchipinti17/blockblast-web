from app.core.errors import ApiError
from app.core.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_password,
)
from app.core.time import isoformat_utc, utc_now
from app.core.validation import is_valid_email, is_valid_password, normalize_email
from app.models import User
from app.repositories import InMemoryStore


class AuthService:
    """Coordinate registration, login, and session heartbeat behavior."""

    def __init__(self, store: InMemoryStore) -> None:
        """Initialize the auth service with a persistence adapter."""
        self._store = store

    def register(self, email: str = "", password: str = "") -> dict:
        """Register a new user and return a success payload."""
        normalized_email = normalize_email(email)
        self._validate_registration(normalized_email, password)

        user = self._store.create_user(normalized_email, hash_password(password))
        if user is None:
            raise ApiError(
                "email_in_use",
                "Email address is already in use.",
                status_code=409,
            )
        return self._success_payload(user)

    def login(self, email: str = "", password: str = "") -> dict:
        """Validate credentials and create a single active session."""
        normalized_email = normalize_email(email)
        user = self._store.get_user_by_email(normalized_email)
        if user is None or not verify_password(password, user.password_hash):
            raise ApiError(
                "invalid_credentials",
                "Email or password is incorrect.",
                status_code=401,
            )

        token = new_session_token()
        self._store.replace_active_session_for_user(user.id, hash_session_token(token))

        payload = self._success_payload(user)
        payload["session_token"] = token
        return payload

    def heartbeat(self, authorization_header: str) -> dict:
        """Validate an active session token and update its heartbeat."""
        token = self._extract_bearer_token(authorization_header)
        updated_session = self._store.touch_session(hash_session_token(token))
        if updated_session is None:
            raise ApiError("invalid_session", "Session is invalid.", status_code=401)

        return {
            "status": "ok",
            "timestamp": isoformat_utc(updated_session.last_seen_at),
        }

    def _validate_registration(self, email: str, password: str) -> None:
        """Validate registration input and uniqueness."""
        if not is_valid_email(email):
            raise ApiError(
                "invalid_email",
                "A valid email address is required.",
                status_code=400,
            )
        if not is_valid_password(password):
            raise ApiError(
                "invalid_password",
                "Password must be at least 8 characters.",
                status_code=400,
            )
        if self._store.get_user_by_email(email) is not None:
            raise ApiError(
                "email_in_use",
                "Email address is already in use.",
                status_code=409,
            )

    def _success_payload(self, user: User) -> dict:
        """Build a standard successful auth payload."""
        return {
            "email": user.email,
            "timestamp": isoformat_utc(utc_now()),
        }

    def _extract_bearer_token(self, authorization_header: str) -> str:
        """Extract a bearer token from the Authorization header."""
        prefix = "Bearer "
        if not authorization_header.startswith(prefix):
            raise ApiError("invalid_session", "Session is invalid.", status_code=401)

        token = authorization_header[len(prefix) :].strip()
        if not token:
            raise ApiError("invalid_session", "Session is invalid.", status_code=401)
        return token
