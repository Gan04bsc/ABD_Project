from flask import Blueprint, jsonify, request

bp = Blueprint("reco_letters", __name__, url_prefix="/api/reco-letters")


@bp.post("/request")
def request_letter():
    data = request.get_json(silent=True) or {}
    return jsonify({"message": "letter requested", "data": data}), 201
