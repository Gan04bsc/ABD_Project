import mimetypes
import os
from flask import Blueprint, jsonify, send_file, current_app, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, csrf
from ..models import User
from ..models.document import Document

bp = Blueprint("users", __name__, url_prefix="/api/users")


def get_current_user() -> User | None:
    ident = get_jwt_identity()
    if ident is None:
        return None
    try:
        user_id = int(ident)
    except (TypeError, ValueError):
        return None
    return User.query.get(user_id)


def resolve_document_path(path: str | None) -> str | None:
    """Resolve legacy/relocated document path to an existing file."""
    if not path:
        return None
    if os.path.exists(path):
        return path

    basename = os.path.basename(path)
    if not basename:
        return None

    candidate = os.path.join(current_app.instance_path, "uploads", basename)
    if os.path.exists(candidate):
        return candidate
    return None


def ensure_teacher(user: User | None):
    if not user:
        return jsonify({"message": "未找到用户"}), 404
    if user.role != "teacher":
        return jsonify({"message": "权限不足，仅教师可访问"}), 403
    return None


def serialize_student(student: User) -> dict:
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "student_id": student.student_id,
        "grade": student.grade,
        "class_name": student.class_name,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    }


def serialize_document(doc: Document) -> dict:
    return {
        "id": doc.id,
        "name": doc.name,
        "original_name": doc.original_name,
        "file_size": doc.file_size,
        "file_type": doc.file_type,
        "category": doc.category,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def serialize_teacher_document(doc: Document, student_id: int) -> dict:
    payload = serialize_document(doc)
    payload["view_url"] = url_for(
        "users.view_student_document",
        student_id=student_id,
        document_id=doc.id,
    )
    payload["download_url"] = url_for(
        "users.download_student_document",
        student_id=student_id,
        document_id=doc.id,
    )
    return payload


@bp.get("/me")
@jwt_required()
def get_me():
    user = get_current_user()
    if not user:
        return jsonify({"message": "未找到用户"}), 404

    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "student_id": user.student_id,
            "grade": user.grade,
            "class_name": user.class_name,
        }
    )


@bp.get("/profile")
@jwt_required()
@csrf.exempt
def profile_get():
    """Self profile only. User id always comes from JWT identity."""
    user = get_current_user()
    if not user:
        return jsonify({"message": "未找到用户"}), 404

    return jsonify(
        {
            "name": user.name,
            "email": user.email,
            "student_id": user.student_id,
            "grade": user.grade,
            "class_name": user.class_name,
            "role": user.role,
        }
    )


@bp.put("/profile")
@jwt_required()
@csrf.exempt
def profile_update():
    """Self profile update only. User id always comes from JWT identity."""
    from flask import request

    user = get_current_user()
    if not user:
        return jsonify({"message": "未找到用户"}), 404

    data = request.get_json(silent=True) or {}
    user.name = data.get("name", user.name)

    # Keep teacher profile less coupled to student fields.
    if user.role == "student":
        user.student_id = data.get("student_id", user.student_id)
        user.grade = data.get("grade", user.grade)
        user.class_name = data.get("class_name", user.class_name)

    db.session.commit()

    return jsonify(
        {
            "message": "保存成功",
            "profile": {
                "name": user.name,
                "email": user.email,
                "student_id": user.student_id,
                "grade": user.grade,
                "class_name": user.class_name,
                "role": user.role,
            },
        }
    )


@bp.get("/students")
@jwt_required()
@csrf.exempt
def get_students():
    """Teacher gets all student records."""
    current_user = get_current_user()
    deny = ensure_teacher(current_user)
    if deny:
        return deny

    students = User.query.filter_by(role="student").order_by(User.created_at.desc()).all()

    students_data = []
    for student in students:
        payload = serialize_student(student)
        payload["document_count"] = Document.query.filter_by(user_id=student.id).count()
        students_data.append(payload)

    return jsonify({"students": students_data, "total": len(students_data)})


@bp.get("/students/<int:student_id>")
@jwt_required()
@csrf.exempt
def get_student_detail(student_id: int):
    """Teacher gets one student's basic info plus document list for detail modal."""
    current_user = get_current_user()
    deny = ensure_teacher(current_user)
    if deny:
        return deny

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"message": "未找到该学生"}), 404

    documents = (
        Document.query.filter_by(user_id=student_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return jsonify(
        {
            "student": serialize_student(student),
            "documents": [serialize_teacher_document(doc, student_id) for doc in documents],
            "document_count": len(documents),
        }
    )


@bp.get("/students/<int:student_id>/documents")
@jwt_required()
@csrf.exempt
def get_student_documents(student_id: int):
    """Teacher-only endpoint for one student's document list."""
    current_user = get_current_user()
    deny = ensure_teacher(current_user)
    if deny:
        return deny

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"message": "未找到该学生"}), 404

    documents = (
        Document.query.filter_by(user_id=student_id)
        .order_by(Document.created_at.desc())
        .all()
    )

    return jsonify(
        {
            "student_id": student_id,
            "documents": [serialize_teacher_document(doc, student_id) for doc in documents],
            "total": len(documents),
        }
    )


@bp.get("/students/<int:student_id>/documents/<int:document_id>/view")
@jwt_required()
@csrf.exempt
def view_student_document(student_id: int, document_id: int):
    """Teacher views a student's document inline."""
    current_user = get_current_user()
    deny = ensure_teacher(current_user)
    if deny:
        return deny

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"message": "未找到该学生"}), 404

    doc = Document.query.filter_by(id=document_id, user_id=student_id).first()
    if not doc:
        return jsonify({"message": "文档不存在"}), 404

    resolved_path = resolve_document_path(doc.file_path)
    if not resolved_path:
        return jsonify({"message": "文件不存在"}), 404

    if doc.file_path != resolved_path:
        doc.file_path = resolved_path
        db.session.commit()

    mime_type, _ = mimetypes.guess_type(doc.original_name or doc.name or "")
    return send_file(
        resolved_path,
        as_attachment=False,
        download_name=doc.original_name or doc.name,
        mimetype=mime_type or "application/octet-stream",
    )


@bp.get("/students/<int:student_id>/documents/<int:document_id>/download")
@jwt_required()
@csrf.exempt
def download_student_document(student_id: int, document_id: int):
    """Teacher downloads a student's document."""
    current_user = get_current_user()
    deny = ensure_teacher(current_user)
    if deny:
        return deny

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"message": "未找到该学生"}), 404

    doc = Document.query.filter_by(id=document_id, user_id=student_id).first()
    if not doc:
        return jsonify({"message": "文档不存在"}), 404

    resolved_path = resolve_document_path(doc.file_path)
    if not resolved_path:
        return jsonify({"message": "文件不存在"}), 404

    if doc.file_path != resolved_path:
        doc.file_path = resolved_path
        db.session.commit()

    mime_type, _ = mimetypes.guess_type(doc.original_name or doc.name or "")
    return send_file(
        resolved_path,
        as_attachment=True,
        download_name=doc.original_name or doc.name,
        mimetype=mime_type or "application/octet-stream",
    )
