import os
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from ..extensions import db, csrf
from ..models import Document, User

bp = Blueprint("documents", __name__, url_prefix="/api/documents")

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

@bp.get("")
@bp.get("/")
@jwt_required()
def list_documents():
    """获取当前用户的所有文档"""
    user_id = get_jwt_identity()
    documents = Document.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": doc.id,
        "name": doc.name,
        "original_name": doc.original_name,
        "file_path": doc.file_path,
        "file_size": doc.file_size,
        "file_type": doc.file_type,
        "created_at": doc.created_at.isoformat() if doc.created_at else None
    } for doc in documents])

@bp.post("")
@bp.post("/")
@jwt_required()
@csrf.exempt
def upload_document():
    """上传文档"""
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"message": "没有选择文件"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "没有选择文件"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"message": "不支持的文件类型"}), 400
    
    try:
        # 生成安全的文件名
        original_filename = secure_filename(file.filename)
        file_extension = get_file_extension(original_filename)
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # 创建上传目录
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 保存到数据库
        document = Document(
            user_id=user_id,
            name=original_filename,
            original_name=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_extension
        )
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            "message": "文件上传成功",
            "document": {
                "id": document.id,
                "name": document.name,
                "file_size": document.file_size,
                "file_type": document.file_type
            }
        }), 201
        
    except Exception as e:
        return jsonify({"message": f"上传失败: {str(e)}"}), 500

@bp.get("/<int:document_id>")
@jwt_required()
def get_document(document_id):
    """获取文档信息"""
    user_id = get_jwt_identity()
    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    
    if not document:
        return jsonify({"message": "文档不存在"}), 404
    
    return jsonify({
        "id": document.id,
        "name": document.name,
        "original_name": document.original_name,
        "file_size": document.file_size,
        "file_type": document.file_type,
        "created_at": document.created_at.isoformat() if document.created_at else None
    })

@bp.get("/<int:document_id>/view")
@jwt_required()
def view_document(document_id):
    """查看文档（在新标签页中打开）"""
    user_id = get_jwt_identity()
    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    
    if not document:
        return jsonify({"message": "文档不存在"}), 404
    
    if not os.path.exists(document.file_path):
        return jsonify({"message": "文件不存在"}), 404
    
    # 根据文件类型设置正确的 MIME 类型
    mime_type = get_mime_type(document.file_type)
    
    return send_file(
        document.file_path,
        as_attachment=False,  # 不强制下载
        mimetype=mime_type
    )

@bp.get("/<int:document_id>/download")
@jwt_required()
def download_document(document_id):
    """下载文档"""
    user_id = get_jwt_identity()
    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    
    if not document:
        return jsonify({"message": "文档不存在"}), 404
    
    if not os.path.exists(document.file_path):
        return jsonify({"message": "文件不存在"}), 404
    
    # 根据文件类型设置正确的 MIME 类型
    mime_type = get_mime_type(document.file_type)
    
    return send_file(
        document.file_path,
        as_attachment=True,  # 强制下载
        download_name=document.original_name,
        mimetype=mime_type
    )

def get_mime_type(file_type):
    """根据文件扩展名获取 MIME 类型"""
    mime_types = {
        'pdf': 'application/pdf',
        'txt': 'text/plain',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif'
    }
    return mime_types.get(file_type.lower(), 'application/octet-stream')

@bp.put("/<int:document_id>")
@jwt_required()
@csrf.exempt
def update_document(document_id):
    """更新文档名称"""
    user_id = get_jwt_identity()
    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    
    if not document:
        return jsonify({"message": "文档不存在"}), 404
    
    data = request.get_json()
    new_name = data.get('name', '').strip()
    
    if not new_name:
        return jsonify({"message": "文档名称不能为空"}), 400
    
    try:
        document.name = new_name
        db.session.commit()
        
        return jsonify({
            "message": "文档名称更新成功",
            "document": {
                "id": document.id,
                "name": document.name,
                "original_name": document.original_name
            }
        })
        
    except Exception as e:
        return jsonify({"message": f"更新失败: {str(e)}"}), 500

@bp.delete("/<int:document_id>")
@jwt_required()
@csrf.exempt
def delete_document(document_id):
    """删除文档"""
    user_id = get_jwt_identity()
    document = Document.query.filter_by(id=document_id, user_id=user_id).first()
    
    if not document:
        return jsonify({"message": "文档不存在"}), 404
    
    try:
        # 删除物理文件
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # 删除数据库记录
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({"message": "文档删除成功"})
        
    except Exception as e:
        return jsonify({"message": f"删除失败: {str(e)}"}), 500
