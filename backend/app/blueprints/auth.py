from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import csrf, db
from ..models import User

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
@csrf.exempt
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = data.get("name") or email.split("@")[0] or "User"
    role = (data.get("role") or "student").strip().lower()

    if role not in {"student", "teacher"}:
        role = "student"

    if not email or not password:
        return jsonify({"message": "email 和 password 必填"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "该邮箱已注册"}), 409

    user = User(email=email, name=name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "registered", "id": user.id}), 201


@bp.post("/login")
@csrf.exempt
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "邮箱或密码错误"}), 401

    claims = {"email": user.email, "role": user.role, "name": user.name}
    identity = str(user.id)
    access = create_access_token(identity=identity, additional_claims=claims)
    refresh = create_refresh_token(identity=identity, additional_claims=claims)

    return (
        jsonify(
            {
                "access_token": access,
                "refresh_token": refresh,
                "role": user.role,
                "user_info": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "student_id": user.student_id,
                    "grade": user.grade,
                    "class_name": user.class_name,
                },
            }
        ),
        200,
    )


@bp.post("/refresh")
@jwt_required(refresh=True)
@csrf.exempt
def refresh():
    ident = get_jwt_identity()
    user = User.query.get(int(ident)) if ident is not None else None
    if not user:
        return jsonify({"message": "用户不存在或已被删除"}), 401

    claims = {"email": user.email, "role": user.role, "name": user.name}
    access = create_access_token(identity=str(user.id), additional_claims=claims)

    return (
        jsonify(
            {
                "access_token": access,
                "role": user.role,
                "user_info": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "student_id": user.student_id,
                    "grade": user.grade,
                    "class_name": user.class_name,
                },
            }
        ),
        200,
    )


@bp.get("/me")
@jwt_required()
def me():
    ident = get_jwt_identity()
    user = User.query.get(int(ident)) if ident is not None else None
    if not user:
        return jsonify({"message": "未找到用户"}), 404
    return jsonify({"id": user.id, "email": user.email, "name": user.name, "role": user.role}), 200
