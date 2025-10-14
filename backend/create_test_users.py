import os
os.environ['FLASK_APP'] = 'wsgi.py'
os.environ['FLASK_ENV'] = 'development'
from app import create_app
from app.extensions import db
from app.models import User

app = create_app()
with app.app_context():
    # 检查是否有用户
    users = User.query.all()
    print(f'当前数据库中有 {len(users)} 个用户')

    if not users:
        print('创建测试用户...')
        # 创建学生用户
        student = User(email='student@test.com', name='学生测试')
        student.set_password('123456')
        student.role = 'student'

        # 创建老师用户
        teacher = User(email='teacher@test.com', name='老师测试')
        teacher.set_password('123456')
        teacher.role = 'teacher'

        db.session.add(student)
        db.session.add(teacher)
        db.session.commit()
        print('测试用户创建成功！')
        print('学生账号: student@test.com / 123456')
        print('老师账号: teacher@test.com / 123456')
    else:
        for user in users:
            print(f'用户: {user.email} (角色: {user.role})')

