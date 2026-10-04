import os
import json
import time
import shutil
import logging
from pathlib import Path
from threading import Lock

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
SESSIONS_FILE = DATA_DIR / "sessions.json"
DEFAULT_TTL = int(os.getenv("FILE_TTL_SECONDS", 86400))  # 24 hours

_memory_lock = Lock()


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not SESSIONS_FILE.exists():
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def _load_sessions_disk() -> dict:
    _ensure_data_dir()
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading sessions.json: {e}")
        return {}


def _save_sessions_disk(sessions: dict):
    _ensure_data_dir()
    temp_file = SESSIONS_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
        temp_file.replace(SESSIONS_FILE)
    except Exception as e:
        logger.error(f"Error saving sessions.json: {e}")


def get_session(session_id: str) -> dict | None:
    with _memory_lock:
        sessions = _load_sessions_disk()
        session = sessions.get(session_id)
        if not session:
            return None

        created_at = session.get("created_at", 0)
        if time.time() - created_at > DEFAULT_TTL:
            _delete_session_unlocked(sessions, session_id)
            _save_sessions_disk(sessions)
            return None

        return session


def set_session(session_id: str, data: dict):
    with _memory_lock:
        sessions = _load_sessions_disk()
        session = sessions.get(session_id, {})
        session.update(data)
        if "created_at" not in session:
            session["created_at"] = time.time()
        session["updated_at"] = time.time()

        sessions[session_id] = session
        _save_sessions_disk(sessions)


def _delete_session_unlocked(sessions: dict, session_id: str):
    session = sessions.pop(session_id, None)
    if session and "temp_dir" in session:
        temp_dir = Path(session["temp_dir"])
        if temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp dir for session {session_id}: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to delete temp dir {temp_dir}: {e}")


def delete_session(session_id: str):
    with _memory_lock:
        sessions = _load_sessions_disk()
        _delete_session_unlocked(sessions, session_id)
        _save_sessions_disk(sessions)


def prune_expired_sessions(ttl_seconds: int = DEFAULT_TTL) -> int:
    """Invoked by the D-06 5-minute background sweeper thread."""
    with _memory_lock:
        sessions = _load_sessions_disk()
        now = time.time()
        expired_ids = [
            sid
            for sid, sdata in sessions.items()
            if now - sdata.get("created_at", now) > ttl_seconds
        ]

        for sid in expired_ids:
            _delete_session_unlocked(sessions, sid)

        if expired_ids:
            _save_sessions_disk(sessions)
            logger.info(f"Pruned {len(expired_ids)} expired session(s).")

        return len(expired_ids)