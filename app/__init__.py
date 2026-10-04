import threading
import time
from flask import Flask
from app.services.session_manager import prune_expired_sessions


def start_session_sweeper():
    """Background thread that prunes expired session files every 5 minutes (D-06/D-07)."""
    def _sweep_loop():
        while True:
            time.sleep(300)  # 5 minutes
            try:
                pruned_count = prune_expired_sessions()
                if pruned_count > 0:
                    print(f"[Session Sweeper] Successfully pruned {pruned_count} expired session(s).")
            except Exception as e:
                print(f"[Session Sweeper Error] Failed during pruning pass: {e}")

    thread = threading.Thread(target=_sweep_loop, daemon=True)
    thread.start()


def create_app():
    app = Flask(__name__)

    # Start the D-07 background session sweeper thread
    start_session_sweeper()

    # Import and register your main routes/blueprints
    # (adjust the import path below to match where your Flask routes are defined)
    try:
        from app.routes import main_bp
        app.register_blueprint(main_bp)
    except ImportError:
        pass  # If you register routes directly on app in app.py, see Step 2

    return app