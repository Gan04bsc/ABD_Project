import os
import uuid
from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..extensions import db, csrf
from ..models import Document

bp = Blueprint("documents", __name__, url_prefix="/api/documents")

# Allowed upload file extensions.
ALLOWED_EXTENSIONS = {
    "txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "ppt", "pptx"
}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def get_current_user_id() -> int | None:
    ident = get_jwt_identity()
    if ident is None:
        return None
    try:
        return int(ident)
    except (TypeError, ValueError):
        return None


def resolve_document_path(path: str | None) -> str | None:
    """Resolve legacy absolute path to current instance uploads path if needed."""
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


@bp.get("")
@bp.get("/")
@jwt_required()
def list_documents():
    """Return all documents for the current JWT user only."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    documents = Document.query.filter_by(user_id=user_id).order_by(Document.created_at.desc()).all()
    return jsonify([
        {
            "id": doc.id,
            "name": doc.name,
            "original_name": doc.original_name,
            "file_path": doc.file_path,
            "file_size": doc.file_size,
            "file_type": doc.file_type,
            "category": doc.category,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
        }
        for doc in documents
    ])


@bp.post("")
@bp.post("/")
@jwt_required()
@csrf.exempt
def upload_document():
    """Upload a document for the current JWT user only."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    if "file" not in request.files:
        return jsonify({"message": "没有选择文件"}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"message": "没有选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "不支持的文件类型"}), 400

    try:
        original_filename = secure_filename(file.filename)
        file_extension = get_file_extension(original_filename)
        unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())

        upload_folder = os.path.join(current_app.instance_path, "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        document = Document(
            user_id=user_id,
            name=original_filename,
            original_name=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_extension,
        )
        db.session.add(document)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "文件上传成功",
                    "document": {
                        "id": document.id,
                        "name": document.name,
                        "file_size": document.file_size,
                        "file_type": document.file_type,
                    },
                }
            ),
            201,
        )
    except Exception as exc:
        return jsonify({"message": f"上传失败: {exc}"}), 500


@bp.get("/<int:document_id>")
@jwt_required()
def get_document(document_id: int):
    """Return metadata for one of current user's documents."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    if not document:
        return jsonify({"message": "文档不存在"}), 404

    return jsonify(
        {
            "id": document.id,
            "name": document.name,
            "original_name": document.original_name,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "category": document.category,
            "created_at": document.created_at.isoformat() if document.created_at else None,
        }
    )


def get_mime_type(file_type: str | None) -> str:
    """Map file extension to MIME type."""
    if not file_type:
        return "application/octet-stream"

    mime_types = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xls": "application/vnd.ms-excel",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
    }
    return mime_types.get(file_type.lower(), "application/octet-stream")


@bp.get("/<int:document_id>/view")
@jwt_required()
def view_document(document_id: int):
    """View one of current user's documents in browser."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    if not document:
        return jsonify({"message": "文档不存在"}), 404

    resolved_path = resolve_document_path(document.file_path)
    if not resolved_path:
        return jsonify({"message": "文件不存在"}), 404

    if document.file_path != resolved_path:
        document.file_path = resolved_path
        db.session.commit()

    return send_file(
        resolved_path,
        as_attachment=False,
        download_name=document.original_name,
        mimetype=get_mime_type(document.file_type),
    )


@bp.get("/<int:document_id>/download")
@jwt_required()
def download_document(document_id: int):
    """Download one of current user's documents."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    if not document:
        return jsonify({"message": "文档不存在"}), 404

    resolved_path = resolve_document_path(document.file_path)
    if not resolved_path:
        return jsonify({"message": "文件不存在"}), 404

    if document.file_path != resolved_path:
        document.file_path = resolved_path
        db.session.commit()

    return send_file(
        resolved_path,
        as_attachment=True,
        download_name=document.original_name,
        mimetype=get_mime_type(document.file_type),
    )


@bp.put("/<int:document_id>")
@jwt_required()
@csrf.exempt
def update_document(document_id: int):
    """Rename one of current user's documents."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    if not document:
        return jsonify({"message": "文档不存在"}), 404

    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return jsonify({"message": "文档名称不能为空"}), 400

    try:
        document.name = new_name
        db.session.commit()
        return jsonify(
            {
                "message": "文档名称更新成功",
                "document": {
                    "id": document.id,
                    "name": document.name,
                    "original_name": document.original_name,
                },
            }
        )
    except Exception as exc:
        return jsonify({"message": f"更新失败: {exc}"}), 500


@bp.delete("/<int:document_id>")
@jwt_required()
@csrf.exempt
def delete_document(document_id: int):
    """Delete one of current user's documents."""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({"message": "未找到用户"}), 404

    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    if not document:
        return jsonify({"message": "文档不存在"}), 404

    try:
        resolved_path = resolve_document_path(document.file_path)
        if resolved_path and os.path.exists(resolved_path):
            os.remove(resolved_path)

        db.session.delete(document)
        db.session.commit()
        return jsonify({"message": "文档删除成功"})
    except Exception as exc:
        return jsonify({"message": f"删除失败: {exc}"}), 500
