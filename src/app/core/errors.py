from flask import jsonify


class ApiError(Exception):
    """Represent an expected API error with a stable code and status."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        """Initialize an API error."""
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_response(error: ApiError):
    """Build a JSON error response from an API error."""
    return (
        jsonify(
            {
                "error": {
                    "code": error.code,
                    "message": error.message,
                }
            }
        ),
        error.status_code,
    )
