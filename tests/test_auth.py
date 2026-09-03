import subprocess
import sys
from pathlib import Path
import pytest


TEST_CASES = [
    ("1", "test_01_successful_register"),
    ("2", "test_02_successful_register_and_login"),
    ("3", "test_03_duplicate_register"),
    ("4", "test_04_unknown_email_login"),
    ("5", "test_05_incorrect_password_login"),
    ("6", "test_06_double_login_invalidates_first_session"),
]


def register_user(client, email="user@example.com", password="correct-password"):
    """Register a user through the API test client."""
    return client.post("/v1/register", json={"email": email, "password": password})


def login_user(client, email="user@example.com", password="correct-password"):
    """Log in a user through the API test client."""
    return client.post("/v1/login", json={"email": email, "password": password})


def heartbeat(client, session_token):
    """Send a heartbeat for a session token."""
    return client.get(
        "/v1/heartbeat",
        headers={"Authorization": f"Bearer {session_token}"},
    )


def test_01_successful_register(client):
    """Register succeeds with a valid email and password."""
    response = register_user(client, email="USER@example.com")
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["email"] == "user@example.com"
    assert "timestamp" in payload


def test_02_successful_register_and_login(client):
    """A registered user can log in and receive a session token."""
    register_user(client)
    response = login_user(client)
    payload = response.get_json()

    assert response.status_code == 200
    assert payload["email"] == "user@example.com"
    assert "timestamp" in payload
    assert "session_token" in payload


def test_03_duplicate_register(client):
    """Register rejects an email address that is already in use."""
    first_response = register_user(client)
    duplicate_response = register_user(client, email="USER@example.com")

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert duplicate_response.get_json()["error"]["code"] == "email_in_use"


def test_04_unknown_email_login(client):
    """Login rejects an email address that does not exist."""
    response = login_user(client, email="missing@example.com")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_05_incorrect_password_login(client):
    """Login rejects a known email with an incorrect password."""
    register_user(client)
    response = login_user(client, password="wrong-password")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "invalid_credentials"


def test_06_double_login_invalidates_first_session(client):
    """A second login on the same account invalidates the first session."""
    register_user(client)

    first_login = login_user(client)
    first_token = first_login.get_json()["session_token"]
    assert heartbeat(client, first_token).status_code == 200

    second_login = login_user(client)
    second_token = second_login.get_json()["session_token"]
    assert second_token != first_token

    first_heartbeat = heartbeat(client, first_token)
    second_heartbeat = heartbeat(client, second_token)

    assert first_heartbeat.status_code == 401
    assert first_heartbeat.get_json()["error"]["code"] == "invalid_session"
    assert second_heartbeat.status_code == 200


def selected_test_node_ids(args: list[str]) -> list[str]:
    """Return pytest node IDs for the selected numeric test arguments."""
    if not args:
        return [str(Path(__file__).resolve())]

    requested_numbers = []
    valid_numbers = {number for number, _ in TEST_CASES}
    for arg in args:
        for number in arg.split(","):
            selected = number.strip()
            if selected and selected not in requested_numbers:
                if selected not in valid_numbers:
                    raise ValueError(selected)
                requested_numbers.append(selected)

    test_names_by_number = dict(TEST_CASES)
    test_file = Path(__file__).resolve()
    return [f"{test_file}::{test_names_by_number[number]}" for number in requested_numbers]


def print_available_tests() -> None:
    """Print the numeric test options supported by this file."""
    print("Available tests:")
    for number, test_name in TEST_CASES:
        print(f"  {number}: {test_name}")


def run_selected_tests(args: list[str]) -> int:
    """Run all tests or the selected numeric tests through pytest."""
    try:
        selected_tests = selected_test_node_ids(args)
    except ValueError as error:
        print(f"Unknown test number: {error}")
        print_available_tests()
        return 2

    return pytest.main(["-v", "--tb=short", *selected_tests])


if __name__ == "__main__":
    raise SystemExit(run_selected_tests(sys.argv[1:]))
