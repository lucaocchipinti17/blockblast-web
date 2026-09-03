import pytest

from app import create_app
from app.repositories import InMemoryStore


@pytest.fixture()
def client():
    """Return a Flask test client with an isolated in-memory store."""
    app = create_app(InMemoryStore())
    app.config.update(TESTING=True)

    with app.test_client() as test_client:
        yield test_client
