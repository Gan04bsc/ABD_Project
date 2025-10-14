from datetime import datetime
from ..extensions import db


class News(db.Model):
    __tablename__ = 'news'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self, include_author: bool = True) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_author:
            # Avoid importing User at module level to prevent circular imports in migrations
            try:
                from .user import User  # local import
                author = User.query.get(self.created_by)
                data["author_name"] = author.name if author else None
            except Exception:
                data["author_name"] = None
        return data




