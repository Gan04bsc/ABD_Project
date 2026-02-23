import os
import re
import uuid
from html import unescape

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ..extensions import csrf, db
from ..models import News, User


bp = Blueprint("news", __name__, url_prefix="/api/news")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "jfif", "avif", "heic", "heif", "tif", "tiff"}
MIME_TO_EXTENSION = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/pjpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/bmp": "bmp",
    "image/x-ms-bmp": "bmp",
    "image/jfif": "jfif",
    "image/avif": "avif",
    "image/heic": "heic",
    "image/heif": "heif",
    "image/tiff": "tiff",
}
NEWS_UPLOAD_SUBDIR = "news_uploads"
MAX_SUMMARY_LENGTH = 180


TAG_DROP_PATTERN = re.compile(r"(?is)<(script|style|iframe|object|embed)[^>]*>.*?</\\1>")
EVENT_ATTR_PATTERN_DOUBLE = re.compile(r'(?i)\son\w+\s*=\s*"[^"]*"')
EVENT_ATTR_PATTERN_SINGLE = re.compile(r"(?i)\son\w+\s*=\s*'[^']*'")
EVENT_ATTR_PATTERN_BARE = re.compile(r"(?i)\son\w+\s*=\s*[^\s>]+")
JS_URI_PATTERN = re.compile(r"(?i)(href|src)\s*=\s*([\"'])\s*javascript:[^\"']*\\2")
IMG_SRC_PATTERN = re.compile(r'(?is)<img[^>]+src=["\']([^"\']+)["\']')
SUMMARY_STRIP_TAG_PATTERN = re.compile(r"(?is)<[^>]+>")


def require_teacher() -> tuple[dict, int] | None:
    """Check teacher permission using JWT claims first, DB fallback second."""
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
        return {"error": "User not found"}, 404
    if user.role != "teacher":
        return {"error": "Teacher role required"}, 403
    return None


def sanitize_news_html(content: str) -> str:
    """Basic backend sanitization as defense-in-depth.

    Frontend still uses DOMPurify before rendering details.
    """
    cleaned = TAG_DROP_PATTERN.sub("", content or "")
    cleaned = EVENT_ATTR_PATTERN_DOUBLE.sub("", cleaned)
    cleaned = EVENT_ATTR_PATTERN_SINGLE.sub("", cleaned)
    cleaned = EVENT_ATTR_PATTERN_BARE.sub("", cleaned)
    cleaned = JS_URI_PATTERN.sub(r"\\1=\\2#\\2", cleaned)
    return cleaned.strip()


def html_to_plain_text(content: str) -> str:
    no_script = TAG_DROP_PATTERN.sub("", content or "")
    no_tag = SUMMARY_STRIP_TAG_PATTERN.sub(" ", no_script)
    text = unescape(no_tag)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_summary(summary: str | None, content: str) -> str:
    candidate = (summary or "").strip()
    if not candidate:
        candidate = html_to_plain_text(content)
    if len(candidate) > MAX_SUMMARY_LENGTH:
        return candidate[:MAX_SUMMARY_LENGTH].rstrip() + "..."
    return candidate


def normalize_cover_image(value) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def extract_cover_from_html(content: str) -> str | None:
    match = IMG_SRC_PATTERN.search(content or "")
    if match:
        src = (match.group(1) or "").strip()
        return src or None
    return None


def ensure_cover_image(cover_image: str | None, content: str) -> str | None:
    return cover_image or extract_cover_from_html(content)


def allowed_image_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def normalize_mimetype(mimetype: str | None) -> str:
    if not mimetype:
        return ""
    return mimetype.split(";", 1)[0].strip().lower()


def resolve_image_extension(filename: str, mimetype: str | None) -> str | None:
    # Prefer extension from sanitized filename.
    safe_name = secure_filename(filename or "")
    if safe_name and "." in safe_name:
        ext = safe_name.rsplit(".", 1)[1].lower()
        if ext in ALLOWED_IMAGE_EXTENSIONS:
            return ext

    # Fallback to extension from raw filename (for rare secure_filename corner cases).
    if filename and "." in filename:
        raw_ext = filename.rsplit(".", 1)[1].lower()
        if raw_ext in ALLOWED_IMAGE_EXTENSIONS:
            return raw_ext

    # Fallback to MIME mapping.
    mime = normalize_mimetype(mimetype)
    return MIME_TO_EXTENSION.get(mime)


@bp.get("")
@bp.get("/")
def list_news():
    keyword = (request.args.get("q") or "").strip().lower()
    items = News.query.order_by(News.created_at.desc()).all()

    if keyword:
        filtered_items = []
        for item in items:
            author_name = None
            try:
                author = User.query.get(item.created_by)
                author_name = author.name if author else ""
            except Exception:
                author_name = ""

            haystack = " ".join(
                [
                    item.title or "",
                    item.summary or "",
                    author_name or "",
                ]
            ).lower()
            if keyword in haystack:
                filtered_items.append(item)
        items = filtered_items

    return jsonify([n.to_dict(include_author=True, include_content=False) for n in items])


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
    raw_content = (data.get("content") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400
    if not raw_content:
        return jsonify({"error": "content is required"}), 400

    content = sanitize_news_html(raw_content)
    if not content:
        return jsonify({"error": "content is empty after sanitization"}), 400

    summary = build_summary(data.get("summary"), content)
    cover_image = ensure_cover_image(normalize_cover_image(data.get("cover_image")), content)

    author_id = int(get_jwt_identity())
    news = News(
        title=title,
        summary=summary,
        cover_image=cover_image,
        content=content,
        created_by=author_id,
    )
    db.session.add(news)
    db.session.commit()
    return jsonify(news.to_dict(include_author=True, include_content=True)), 201


@bp.get("/<int:news_id>")
def get_news(news_id: int):
    news = News.query.get(news_id)
    if not news:
        return jsonify({"error": "not found"}), 404
    return jsonify(news.to_dict(include_author=True, include_content=True))


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
        return jsonify({"error": "not found"}), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = (data.get("title") or "").strip()
        if not title:
            return jsonify({"error": "title cannot be empty"}), 400
        news.title = title

    if "content" in data:
        content_raw = (data.get("content") or "").strip()
        if not content_raw:
            return jsonify({"error": "content cannot be empty"}), 400
        sanitized = sanitize_news_html(content_raw)
        if not sanitized:
            return jsonify({"error": "content is empty after sanitization"}), 400
        news.content = sanitized

    if "summary" in data:
        news.summary = build_summary(data.get("summary"), news.content)
    elif "content" in data and not (news.summary or "").strip():
        news.summary = build_summary("", news.content)

    if "cover_image" in data:
        requested_cover = normalize_cover_image(data.get("cover_image"))
        news.cover_image = ensure_cover_image(requested_cover, news.content)
    elif "content" in data and not news.cover_image:
        news.cover_image = ensure_cover_image(None, news.content)

    db.session.commit()
    return jsonify(news.to_dict(include_author=True, include_content=True))


@bp.delete("/<int:news_id>")
@jwt_required()
@csrf.exempt
def delete_news(news_id: int):
    perm = require_teacher()
    if perm is not None:
        return perm

    news = News.query.get(news_id)
    if not news:
        return jsonify({"error": "not found"}), 404

    db.session.delete(news)
    db.session.commit()
    return jsonify({"message": "deleted"})


@bp.post("/upload_image")
@jwt_required()
@csrf.exempt
def upload_news_image():
    perm = require_teacher()
    if perm is not None:
        return perm

    if "file" not in request.files:
        return jsonify({"error": "file field is required"}), 400

    image = request.files["file"]
    if not image or not image.filename:
        return jsonify({"error": "image is required"}), 400

    ext = resolve_image_extension(image.filename, image.mimetype)
    if not ext:
        return jsonify(
            {
                "error": "unsupported image type",
                "filename": image.filename,
                "mimetype": normalize_mimetype(image.mimetype),
            }
        ), 400

    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.instance_path, NEWS_UPLOAD_SUBDIR)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)
    image.save(file_path)

    return jsonify(
        {
            "url": f"/api/news/images/{filename}",
            "filename": filename,
        }
    ), 201


@bp.get("/images/<path:filename>")
def serve_news_image(filename: str):
    safe_name = secure_filename(filename)
    if not safe_name or safe_name != filename:
        return jsonify({"error": "invalid filename"}), 400

    upload_dir = os.path.join(current_app.instance_path, NEWS_UPLOAD_SUBDIR)
    return send_from_directory(upload_dir, safe_name)
