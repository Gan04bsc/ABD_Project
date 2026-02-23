from datetime import datetime

from ..extensions import db


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False, default="")
    cover_image = db.Column(db.String(1024), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self, include_author: bool = True, include_content: bool = True) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "summary": self.summary or "",
            "cover_image": self.cover_image,
            "created_by": self.created_by,
            "author_id": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data["content"] = self.content
        if include_author:
            # Local import avoids circular import issues during migrations.
            try:
                from .user import User

                author = User.query.get(self.created_by)
                data["author_name"] = author.name if author else None
            except Exception:
                data["author_name"] = None
        return data
