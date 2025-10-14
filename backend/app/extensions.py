from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

# Flask extensions instances

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
csrf = CSRFProtect()
# 使用最通用的 "threading"，避免在 CLI 环境（如 flask db ...）初始化时因缺少异步后端而报错。
socketio = SocketIO(async_mode="threading", manage_session=False)


# Celery integration (optional, lightweight stub)
from celery import Celery

def make_celery(app=None) -> Celery:
    app = app or None
    broker = None
    backend = None
    if app:
        broker = app.config.get("CELERY_BROKER_URL")
        backend = app.config.get("CELERY_RESULT_BACKEND")
    celery = Celery(__name__, broker=broker, backend=backend)
    if app:
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
    return celery
