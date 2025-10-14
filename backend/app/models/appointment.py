from datetime import datetime
from ..extensions import db


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(32), nullable=False)  # 格式: "09:00-10:00"
    appointment_type = db.Column(db.String(64), nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(32), default='pending')  # pending, approved, rejected, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    student = db.relationship('User', foreign_keys=[student_id], backref='appointments_as_student')
    teacher = db.relationship('User', foreign_keys=[teacher_id], backref='appointments_as_teacher')
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'teacher_id': self.teacher_id,
            'student': {
                'name': self.student.name,
                'email': self.student.email,
                'student_id': self.student.student_id,
                'grade': self.student.grade,
                'class_name': self.student.class_name
            } if self.student else None,
            'teacher': {
                'name': self.teacher.name,
                'email': self.teacher.email
            } if self.teacher else None,
            'appointment_date': self.appointment_date.isoformat() if self.appointment_date else None,
            'time_slot': self.time_slot,
            'appointment_type': self.appointment_type,
            'reason': self.reason,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Appointment {self.id} {self.student_id}->{self.teacher_id} on {self.appointment_date} {self.time_slot}>'

