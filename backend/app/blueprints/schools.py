from flask import Blueprint, jsonify

bp = Blueprint("schools", __name__, url_prefix="/api/schools")


@bp.get("")
@bp.get("/")
def list_schools():
    return jsonify([{"id": 1, "name": "Example University", "city": "Boston"}])
