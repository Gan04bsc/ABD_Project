from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, date
from ..models import Appointment, User
from ..extensions import db

bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')


@bp.get('/slots')
def get_slots():
    return jsonify([{'id': 1, 'teacher_id': 100, 'start': '2025-01-01T10:00:00Z'}])


@bp.get('/booked-slots/<int:teacher_id>')
def get_booked_slots(teacher_id):
    """获取指定老师的已预约时间段"""
    appointment_date = request.args.get('date')
    
    if not appointment_date:
        return jsonify({'error': '请提供日期参数'}), 400
    
    try:
        target_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误，应为YYYY-MM-DD'}), 400
    
    # 查询该老师在指定日期的已确认预约（pending和approved状态）
    booked_appointments = Appointment.query.filter(
        Appointment.teacher_id == teacher_id,
        Appointment.appointment_date == target_date,
        Appointment.status.in_(['pending', 'approved'])
    ).all()
    
    booked_slots = [apt.time_slot for apt in booked_appointments]
    
    return jsonify({
        'date': appointment_date,
        'teacher_id': teacher_id,
        'booked_slots': booked_slots
    })


@bp.post('/book')
@jwt_required()
def book_slot():
    """创建预约"""
    data = request.get_json(silent=True) or {}
    current_user_id = int(get_jwt_identity())
    
    # 验证必填字段
    required_fields = ['teacher_id', 'appointment_date', 'time_slot', 'appointment_type']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    try:
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': '日期格式错误'}), 400
    
    # 检查时间段是否已被预约
    existing = Appointment.query.filter(
        Appointment.teacher_id == data['teacher_id'],
        Appointment.appointment_date == appointment_date,
        Appointment.time_slot == data['time_slot'],
        Appointment.status.in_(['pending', 'approved'])
    ).first()
    
    if existing:
        return jsonify({'error': '该时间段已被预约'}), 409
    
    # 创建预约
    appointment = Appointment(
        student_id=current_user_id,
        teacher_id=data['teacher_id'],
        appointment_date=appointment_date,
        time_slot=data['time_slot'],
        appointment_type=data['appointment_type'],
        reason=data.get('reason', ''),
        status='pending'
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    return jsonify({
        'message': '预约创建成功',
        'appointment': appointment.to_dict()
    }), 201


@bp.get('/appointments')
@jwt_required()
def get_appointments():
    """获取当前用户的预约列表"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    status = request.args.get('status')
    
    # 根据用户角色返回不同的预约列表
    if user.role == 'teacher':
        query = Appointment.query.filter_by(teacher_id=current_user_id)
    else:
        query = Appointment.query.filter_by(student_id=current_user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(Appointment.created_at.desc()).all()
    
    return jsonify({
        'appointments': [apt.to_dict() for apt in appointments]
    })


@bp.patch('/appointments/<int:appointment_id>')
@jwt_required()
def update_appointment(appointment_id):
    """更新预约状态（老师确认/拒绝，学生取消）"""
    current_user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    
    appointment = Appointment.query.get(appointment_id)
    
    if not appointment:
        return jsonify({'error': '预约不存在'}), 404
    
    # 获取当前用户
    user = User.query.get(current_user_id)
    
    # 权限验证
    is_teacher = appointment.teacher_id == current_user_id
    is_student = appointment.student_id == current_user_id
    
    if not (is_teacher or is_student):
        return jsonify({'error': '无权限修改此预约'}), 403
    
    # 更新状态
    if 'status' in data:
        new_status = data['status']
        
        # 学生只能取消自己的预约
        if is_student and not is_teacher:
            if new_status != 'cancelled':
                return jsonify({'error': '学生只能取消预约'}), 403
        
        appointment.status = new_status
    
    db.session.commit()
    
    return jsonify({
        'message': '预约状态已更新',
        'appointment': appointment.to_dict()
    })
