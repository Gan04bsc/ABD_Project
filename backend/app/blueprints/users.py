import mimetypes
import os
from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db, csrf
from ..models import User
from ..models.document import Document

bp = Blueprint("users", __name__, url_prefix="/api/users")


def resolve_document_path(path: str | None) -> str | None:
    """Resolve legacy/relocated document path to an existing file."""
    if not path:
        return None
    if os.path.exists(path):
        return path

    # Fallback: use current instance/uploads + basename for migrated workspace roots.
    basename = os.path.basename(path)
    if not basename:
        return None

    candidate = os.path.join(current_app.instance_path, "uploads", basename)
    if os.path.exists(candidate):
        return candidate
    return None


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


@bp.get("/students")
@jwt_required()
@csrf.exempt
def get_students():
    """获取所有学生列表（仅教师可访问）"""
    ident = get_jwt_identity()
    current_user = User.query.get(int(ident)) if ident is not None else None
    
    if not current_user:
        return jsonify({"message": "未找到用户"}), 404
    
    # 权限检查：仅教师可访问
    if current_user.role != "teacher":
        return jsonify({"message": "权限不足，仅教师可访问"}), 403
    
    # 获取所有学生
    students = User.query.filter_by(role="student").order_by(User.created_at.desc()).all()
    
    students_data = []
    for student in students:
        # 统计学生上传的文档数量
        doc_count = Document.query.filter_by(user_id=student.id).count()
        
        students_data.append({
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "student_id": student.student_id,
            "grade": student.grade,
            "class_name": student.class_name,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "document_count": doc_count,
        })
    
    return jsonify({
        "students": students_data,
        "total": len(students_data),
    })


@bp.get("/students/<int:student_id>")
@jwt_required()
@csrf.exempt
def get_student_detail(student_id):
    """获取指定学生的详细信息及其上传的文档（仅教师可访问）"""
    ident = get_jwt_identity()
    current_user = User.query.get(int(ident)) if ident is not None else None
    
    if not current_user:
        return jsonify({"message": "未找到用户"}), 404
    
    # 权限检查：仅教师可访问
    if current_user.role != "teacher":
        return jsonify({"message": "权限不足，仅教师可访问"}), 403
    
    # 获取指定学生
    student = User.query.get(student_id)
    if not student:
        return jsonify({"message": "未找到该学生"}), 404
    
    if student.role != "student":
        return jsonify({"message": "该用户不是学生"}), 400
    
    # 获取学生上传的所有文档
    documents = Document.query.filter_by(user_id=student_id).order_by(Document.created_at.desc()).all()
    
    documents_data = []
    for doc in documents:
        documents_data.append({
            "id": doc.id,
            "name": doc.name,
            "original_name": doc.original_name,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "category": doc.category,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        })
    
    return jsonify({
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "student_id": student.student_id,
            "grade": student.grade,
            "class_name": student.class_name,
            "created_at": student.created_at.isoformat() if student.created_at else None,
        },
        "documents": documents_data,
        "document_count": len(documents_data),
    })


@bp.get("/students/<int:student_id>/documents/<int:document_id>/view")
@jwt_required()
@csrf.exempt
def view_student_document(student_id: int, document_id: int):
    """教师查看学生上传的文档内容（在线预览）。"""
    ident = get_jwt_identity()
    current_user = User.query.get(int(ident)) if ident is not None else None
    if not current_user:
        return jsonify({"message": "未找到用户"}), 404

    if current_user.role != "teacher":
        return jsonify({"message": "权限不足，仅教师可访问"}), 403

    student = User.query.get(student_id)
    if not student or student.role != "student":
        return jsonify({"message": "未找到该学生"}), 404

    doc = Document.query.filter_by(id=document_id, user_id=student_id).first()
    if not doc:
        return jsonify({"message": "文档不存在"}), 404

    resolved_path = resolve_document_path(doc.file_path)
    if not resolved_path:
        return jsonify({"message": "文件不存在"}), 404

    # Auto-heal stale absolute paths in database.
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
