import os
from app import create_app, socketio

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    # For SocketIO support with eventlet/gevent; falls back to werkzeug in dev
    socketio.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
