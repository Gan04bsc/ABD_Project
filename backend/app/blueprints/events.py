from flask import Blueprint, jsonify, request

bp = Blueprint("events", __name__, url_prefix="/api/events")


@bp.get("")
@bp.get("/")
def list_events():
    return jsonify([{"id": 1, "title": "Study Abroad 101", "time": "2025-01-05T08:00:00Z"}])


@bp.post("/register")
def register_event():
    data = request.get_json(silent=True) or {}
    return jsonify({"message": "registered to event", "data": data}), 201
