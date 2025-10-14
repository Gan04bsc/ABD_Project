from datetime import datetime
from ..extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False, default="User")
    role = db.Column(db.String(32), nullable=False, default="student")
    password_hash = db.Column(db.String(255), nullable=False)
    student_id = db.Column(db.String(32))
    grade = db.Column(db.String(16))
    class_name = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email}>"
