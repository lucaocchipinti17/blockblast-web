from flask import Flask

from app.api.routes.auth import auth_bp
from app.api.routes.health import health_bp
from app.repositories import InMemoryStore
from app.services.auth_service import AuthService


def create_app(store: InMemoryStore | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["AUTH_SERVICE"] = AuthService(store or InMemoryStore())

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix="/v1")

    return app
