from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, csrf
from ..models import User

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.get("/me")
@jwt_required()
def get_me():
    ident = get_jwt_identity()
    user = User.query.get(int(ident)) if ident is not None else None
    if not user:
        return jsonify({"message": "未找到用户"}), 404
    return jsonify({
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "student_id": user.student_id,
        "grade": user.grade,
        "class_name": user.class_name,
    })


@bp.get("/profile")
@jwt_required()
@csrf.exempt
def profile_get():
    ident = get_jwt_identity()
    user = User.query.get(int(ident)) if ident is not None else None
    if not user:
        return jsonify({"message": "未找到用户"}), 404
    return jsonify({
        "name": user.name,
        "student_id": user.student_id,
        "grade": user.grade,
        "class_name": user.class_name,
    })


@bp.put("/profile")
@jwt_required()
@csrf.exempt
def profile_update():
    ident = get_jwt_identity()
    user = User.query.get(int(ident)) if ident is not None else None
    if not user:
        return jsonify({"message": "未找到用户"}), 404
    data = request.get_json(silent=True) or {}
    user.name = data.get("name", user.name)
    user.student_id = data.get("student_id", user.student_id)
    user.grade = data.get("grade", user.grade)
    user.class_name = data.get("class_name", user.class_name)
    db.session.commit()
    return jsonify({
        "message": "保存成功",
        "profile": {
            "name": user.name,
            "student_id": user.student_id,
            "grade": user.grade,
            "class_name": user.class_name,
        },
    })
