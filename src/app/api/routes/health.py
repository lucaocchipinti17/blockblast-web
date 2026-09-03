from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Return the API health status."""
    return jsonify({"status": "ok"}), 200
