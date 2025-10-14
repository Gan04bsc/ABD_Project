from flask import Blueprint, jsonify, request

bp = Blueprint("schedule", __name__, url_prefix="/api/schedule")


@bp.get("/slots")
def get_slots():
    return jsonify([{"id": 1, "teacher_id": 100, "start": "2025-01-01T10:00:00Z"}])


@bp.post("/book")
def book_slot():
    data = request.get_json(silent=True) or {}
    return jsonify({"message": "booked", "data": data}), 201
