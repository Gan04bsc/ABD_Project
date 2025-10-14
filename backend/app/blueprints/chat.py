from flask import Blueprint, jsonify
from ..extensions import socketio

bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.get("/history")
def chat_history():
    return jsonify([{"id": 1, "from": 1, "to": 2, "text": "Hello"}])


@socketio.on("message")
def handle_message(msg):
    # Echo message to all clients
    socketio.emit("message", msg)
