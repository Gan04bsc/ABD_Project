from datetime import datetime
from ..extensions import db


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)  # 显示名称（可修改）
    original_name = db.Column(db.String(255), nullable=False)  # 原始文件名
    file_path = db.Column(db.String(1024), nullable=False)  # 文件存储路径
    file_size = db.Column(db.Integer, nullable=False, default=0)  # 文件大小（字节）
    file_type = db.Column(db.String(32), nullable=False)  # 文件类型/扩展名
    category = db.Column(db.String(64), nullable=False, default="general")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("documents", lazy=True))
