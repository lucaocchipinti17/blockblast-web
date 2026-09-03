import hashlib
import secrets

from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    """Hash a plaintext password for storage."""
    return generate_password_hash(password, method="scrypt")


def verify_password(password: str, password_hash: str) -> bool:
    """Return whether a plaintext password matches a stored hash."""
    return check_password_hash(password_hash, password)


def new_session_token() -> str:
    """Create a cryptographically secure opaque session token."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> str:
    """Hash a session token before lookup or storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
