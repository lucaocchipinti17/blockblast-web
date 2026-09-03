from threading import RLock
from uuid import uuid4

from app.core.time import utc_now
from app.models import Session, User


class InMemoryStore:
    """Store users and sessions in memory for the first API draft."""

    def __init__(self) -> None:
        """Initialize empty user and session collections."""
        self._lock = RLock()
        self._users_by_id: dict[str, User] = {}
        self._user_ids_by_email: dict[str, str] = {}
        self._sessions_by_token_hash: dict[str, Session] = {}
        self._active_token_hash_by_user_id: dict[str, str] = {}

    def create_user(self, email: str, password_hash: str) -> User | None:
        """Create and store a new user unless the email already exists."""
        with self._lock:
            if email in self._user_ids_by_email:
                return None

            user = User(
                id=str(uuid4()),
                email=email,
                password_hash=password_hash,
                created_at=utc_now(),
            )
            self._users_by_id[user.id] = user
            self._user_ids_by_email[user.email] = user.id
            return user

    def get_user_by_email(self, email: str) -> User | None:
        """Return a user by normalized email address."""
        with self._lock:
            user_id = self._user_ids_by_email.get(email)
            if user_id is None:
                return None
            return self._users_by_id[user_id]

    def replace_active_session_for_user(self, user_id: str, token_hash: str) -> Session:
        """Replace a user's active session with one keyed by token hash."""
        with self._lock:
            active_token_hash = self._active_token_hash_by_user_id.get(user_id)
            if active_token_hash == token_hash:
                session = self.get_session_by_token_hash(token_hash)
                if session is not None and session.revoked_at is None:
                    return session

            if active_token_hash is not None:
                self.revoke_session(active_token_hash)

            session = self._create_session(user_id, token_hash)
            self._active_token_hash_by_user_id[user_id] = token_hash
            return session

    def get_session_by_token_hash(self, token_hash: str) -> Session | None:
        """Return a session by hashed session token."""
        with self._lock:
            return self._sessions_by_token_hash.get(token_hash)

    def revoke_session(self, token_hash: str) -> Session | None:
        """Remove an active session by token hash."""
        with self._lock:
            session = self.get_session_by_token_hash(token_hash)
            if session is None:
                return None

            del self._sessions_by_token_hash[token_hash]

            active_token_hash = self._active_token_hash_by_user_id.get(session.user_id)
            if active_token_hash == token_hash:
                del self._active_token_hash_by_user_id[session.user_id]

            return session

    def touch_session(self, token_hash: str) -> Session | None:
        """Update a session heartbeat timestamp."""
        with self._lock:
            session = self.get_session_by_token_hash(token_hash)
            if session is None or session.revoked_at is not None:
                return None

            active_token_hash = self._active_token_hash_by_user_id.get(session.user_id)
            if active_token_hash != token_hash:
                return None

            updated = Session(
                user_id=session.user_id,
                token_hash=session.token_hash,
                created_at=session.created_at,
                last_seen_at=utc_now(),
                revoked_at=session.revoked_at,
            )
            self._sessions_by_token_hash[token_hash] = updated
            return updated

    def _create_session(self, user_id: str, token_hash: str) -> Session:
        """Create and store a new active session keyed by token hash."""
        now = utc_now()
        session = Session(
            user_id=user_id,
            token_hash=token_hash,
            created_at=now,
            last_seen_at=now,
        )
        self._sessions_by_token_hash[token_hash] = session
        return session
