from flask import Blueprint, current_app, jsonify, request

from app.core.errors import ApiError, error_response
from app.services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__)


def get_auth_service() -> AuthService:
    """Return the configured authentication service."""
    return current_app.config["AUTH_SERVICE"]


def get_json_body() -> dict:
    """Return the request JSON body or raise a standard API error."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError(
            "invalid_request",
            "Request body must be a JSON object.",
            status_code=400,
        )
    return body


@auth_bp.errorhandler(ApiError)
def handle_api_error(error: ApiError):
    """Convert known API errors into JSON responses."""
    return error_response(error)


@auth_bp.post("/register")
def register():
    """Register a new user account."""
    body = get_json_body()
    result = get_auth_service().register(
        email=body.get("email", ""),
        password=body.get("password", ""),
    )
    return jsonify(result), 200


@auth_bp.post("/login")
def login():
    """Log in a user and create a single active session."""
    body = get_json_body()
    result = get_auth_service().login(
        email=body.get("email", ""),
        password=body.get("password", ""),
    )
    return jsonify(result), 200


@auth_bp.get("/heartbeat")
def heartbeat():
    """Confirm that the supplied session token is still active."""
    token = request.headers.get("Authorization", "")
    result = get_auth_service().heartbeat(token)
    return jsonify(result), 200
