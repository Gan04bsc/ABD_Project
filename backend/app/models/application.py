from datetime import datetime
from ..extensions import db


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey("school.id"), nullable=False)
    status = db.Column(db.String(32), default="draft")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("applications", lazy=True))
    school = db.relationship("School", backref=db.backref("applications", lazy=True))
