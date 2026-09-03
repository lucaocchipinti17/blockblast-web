# Block Blast Web/API Journal

## Day 1: Building the First API Foundation

### Personal Note

This project is partly a way for me to refresh my web development skills and partly a way to create added support for the Block Blast platform. The goal is not just to make endpoints that work, but to build the backend in a way that feels clean, understandable, secure, and easy to extend as the product grows.

Today was about laying the first small foundation: a Flask API that can register users, log them in, keep track of active sessions, and enforce the important rule that one account can only be active on one device at a time.

## What We Built

The first version of the API supports:

- `GET /health`
- `POST /v1/register`
- `POST /v1/login`
- `GET /v1/heartbeat`

The code is split into a few focused areas:

- `src/app/api/routes/` handles HTTP routes.
- `src/app/services/` handles application logic.
- `src/app/repositories.py` handles storage.
- `src/app/models.py` defines the core data objects.
- `src/app/core/` holds shared utilities for errors, security, time, and validation.
- `tests/` contains the API tests.

This is intentionally small, but the boundaries matter. Routes should not know the details of session replacement. Services should not care whether data is stored in memory today or PostgreSQL later. The repository can change without forcing the whole API to change with it.

## Why Flask

I decided to keep the API layer in Flask because this project is still early and Flask keeps the surface area small. It is easy to read, easy to run, and does not hide much magic.

FastAPI would still be a strong alternative later, especially for larger typed APIs and automatic schema validation. But for Day 1, Flask is enough, and keeping the stack familiar lets me focus on the actual auth/session behavior instead of framework overhead.

## Registration

The register endpoint accepts an email and password, validates the email format, checks that the email is not already in use, hashes the password, and returns a success payload with:

- email address
- timestamp

Email addresses are normalized to lowercase before storage. That means `User@example.com` and `user@example.com` are treated as the same account.

The email validation is deliberately simple. It catches obvious invalid input, but it is not trying to perfectly implement every edge case in the email specification. Long term, real account ownership should come from email verification, not from a massive regex.

## Login And Sessions

When a user logs in successfully, the server creates a new opaque session token and returns it to the client.

The client receives the raw token. The server stores only a hash of that token.

That gives us a cleaner security model:

- If storage is inspected, raw session tokens are not sitting there in plaintext.
- The server remains the source of truth for whether a session is active.
- Sessions can be invalidated immediately.

This is why opaque tokens are a better fit here than stateless JWTs. JWTs are useful in some systems, but this app has a hard product rule: logging in on one device should log out the previous device. With JWTs, immediate revocation usually requires adding server-side session checks anyway. Once we need that lookup, opaque tokens are simpler and more direct.

## One Active Device

The key login rule is:

> A successful login replaces any existing active session for the same user.

The in-memory store uses two indexes:

```text
token_hash -> session
user_id -> active_token_hash
```

That gives us constant-time lookups for the important paths.

On login:

```text
email -> user
user.id -> current active token hash
remove old session if it exists
create new session
store new active token hash for user
```

On heartbeat:

```text
raw token -> token hash
token hash -> session
session.user_id -> active token hash
confirm token hash is still active
update last_seen_at
```

This avoids scanning all sessions to find the one belonging to a user. That matters because session checks happen often and should stay fast as the number of users grows.

## Heartbeat

The desktop app is expected to ping the server every 30 minutes while running. The first version of the heartbeat endpoint checks whether the current token still belongs to the user's active session.

If the token is valid, the server updates the session's `last_seen_at` timestamp and returns `200 OK`.

If the token has been replaced by a newer login, heartbeat returns an `invalid_session` error. This is how the first device learns it has been logged out after the same account logs in somewhere else.

Long term, the heartbeat should probably enforce session expiration too. The client should log out when heartbeat fails, and the server should reject expired sessions even if the client does not behave correctly. The client gives a better user experience; the server is the actual security boundary.

## Testing

The first test suite focuses on the core auth behavior:

1. Successful register
2. Successful register and login
3. Duplicate register
4. Unknown email login
5. Incorrect password login
6. Double login invalidates the first session

The tests use Flask's test client from `tests/conftest.py`, so each test gets a fresh isolated app and in-memory store.

The test file can be run directly:

```bash
python3 tests/test_auth.py
```

Specific tests can be selected by number:

```bash
python3 tests/test_auth.py 1 6
python3 tests/test_auth.py 2,4
```

Under the hood, this uses pytest. That keeps the runtime support simple while still giving clear terminal output for each test.

## What Comes Next

The current storage layer is in memory, which is fine for the first draft but not enough for production. The next major step is replacing it with a real database-backed repository, likely PostgreSQL.

After that, the natural next pieces are:

- logout endpoint
- dummy purchase endpoint
- license model
- session expiration
- rate limiting
- structured app config
- migration support

Day 1 is intentionally modest. The win is that the project now has a readable Flask API foundation, tested auth flows, and a session design that matches the desktop app's one-device-at-a-time rule.
