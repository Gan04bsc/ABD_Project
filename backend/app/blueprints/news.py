from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db, csrf
from ..models import News, User


bp = Blueprint("news", __name__, url_prefix="/api/news")


def require_teacher() -> tuple[dict, int] | None:
    """Check teacher permission.

    Prefer role from JWT claims for performance; if missing or not teacher,
    fall back to querying the database using current identity to avoid issues
    with legacy tokens that lack claims.
    """
    try:
        claims = get_jwt()
        role = claims.get("role") if claims else None
    except Exception:
        role = None

    if role == "teacher":
        return None

    ident = get_jwt_identity()
    try:
        user_id = int(ident) if ident is not None else None
    except Exception:
        user_id = None
    user = User.query.get(user_id) if user_id is not None else None
    if not user:
        return {"error": "未找到用户"}, 404
    if user.role != "teacher":
        return {"error": "仅老师可执行此操作"}, 403
    return None


@bp.get("")
@bp.get("/")
def list_news():
    items = News.query.order_by(News.created_at.desc()).all()
    return jsonify([n.to_dict(include_author=True) for n in items])


@bp.post("")
@bp.post("/")
@jwt_required()
@csrf.exempt
def create_news():
    perm = require_teacher()
    if perm is not None:
        return perm

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"error": "标题与内容均为必填"}), 400

    author_id = int(get_jwt_identity())
    news = News(title=title, content=content, created_by=author_id)
    db.session.add(news)
    db.session.commit()
    return jsonify(news.to_dict(include_author=True)), 201


@bp.get("/<int:news_id>")
def get_news(news_id: int):
    news = News.query.get(news_id)
    if not news:
        return jsonify({"error": "未找到"}), 404
    return jsonify(news.to_dict(include_author=True))


@bp.put("/<int:news_id>")
@bp.patch("/<int:news_id>")
@jwt_required()
@csrf.exempt
def update_news(news_id: int):
    perm = require_teacher()
    if perm is not None:
        return perm

    news = News.query.get(news_id)
    if not news:
        return jsonify({"error": "未找到"}), 404

    data = request.get_json(silent=True) or {}
    title = data.get("title")
    content = data.get("content")
    if title is not None:
        title = title.strip()
        if not title:
            return jsonify({"error": "标题不能为空"}), 400
        news.title = title
    if content is not None:
        content = content.strip()
        if not content:
            return jsonify({"error": "内容不能为空"}), 400
        news.content = content
    db.session.commit()
    return jsonify(news.to_dict())


@bp.delete("/<int:news_id>")
@jwt_required()
@csrf.exempt
def delete_news(news_id: int):
    perm = require_teacher()
    if perm is not None:
        return perm

    news = News.query.get(news_id)
    if not news:
        return jsonify({"error": "未找到"}), 404
    db.session.delete(news)
    db.session.commit()
    return jsonify({"message": "已删除"})




