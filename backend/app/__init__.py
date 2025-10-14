import os
from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path

from .config import get_config
from .extensions import db, migrate, jwt, cors, csrf, socketio


def register_blueprints(app: Flask) -> None:
    """Import and register all blueprints here to avoid circular imports."""
    from .blueprints.auth import bp as auth_bp
    from .blueprints.users import bp as users_bp
    from .blueprints.documents import bp as documents_bp
    from .blueprints.chat import bp as chat_bp
    from .blueprints.schedule import bp as schedule_bp
    from .blueprints.reco_letters import bp as reco_letters_bp
    from .blueprints.schools import bp as schools_bp
    from .blueprints.events import bp as events_bp
    from .blueprints.news import bp as news_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(reco_letters_bp)
    app.register_blueprint(schools_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(news_bp)


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    # Load config
    app.config.from_object(get_config(config_name))

    # Init extensions
    db.init_app(app)
    # 确保模型被导入，使得 Alembic 能发现元数据
    with app.app_context():
        from . import models  # noqa: F401
    migrate.init_app(app, db)
    jwt.init_app(app)
    # CORS：允许所有来源，特别是本地开发
    cors.init_app(
        app,
        resources={
            r"/*": {
                "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5000", "http://127.0.0.1:5000", "*"]
            }
        },
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    # 不启用CSRF保护，因为使用JWT认证
    # csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", ["*"]))

    # Simple health check
    @app.get("/health")
    def health() -> tuple[dict, int]:
        return {"status": "ok"}, 200

    # Register blueprints
    register_blueprints(app)

    # 避免 API 响应被缓存，确保读取到最新数据
    @app.after_request
    def add_no_cache_headers(response):
        try:
            if request.path.startswith('/api/'):
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
        except Exception:
            pass
        return response

    # Serve frontend (index.html and assets) from project frontend directory
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    FRONTEND_DIR = PROJECT_ROOT / "frontend"

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_frontend(path: str):
        # Avoid intercepting API routes
        if path.startswith("api/"):
            return jsonify({"message": "Not Found"}), 404
        target = FRONTEND_DIR / path
        if path and target.is_file():
            return send_from_directory(FRONTEND_DIR, path)
        # fallback to index.html
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return send_from_directory(FRONTEND_DIR, "index.html")
        return jsonify({"message": "frontend not found"}), 404

    return app
