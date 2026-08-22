"""Persistent store for the editor-managed acronym allow-list.

The list lives as a JSON file on the server filesystem. The path is
`os.environ["ACRONYM_DB_PATH"]` if set (this is the hook for mounting a
Railway Volume in production), otherwise it falls back to the in-repo seed
file at ``app/data/acronyms.json``.

If the file is missing or empty, we re-seed from the bundled file so the
service comes up with a usable list even on a fresh volume mount.

Writes are atomic (write-temp + ``os.replace``) so an interrupted save can
never leave the file half-written.
"""

from __future__ import annotations

import json
import os
import shutil
import threading
from copy import deepcopy
from pathlib import Path

# Bundled seed file — also the default location when no env override is set.
_SEED_PATH = Path(__file__).resolve().parent.parent / "data" / "acronyms.json"

# A single in-process lock keeps reads/writes consistent under Flask's
# threaded server. Multiple gunicorn workers would still race; for that, the
# atomic rename is the safety net.
_lock = threading.Lock()


def _store_path() -> Path:
    override = os.environ.get("ACRONYM_DB_PATH")
    return Path(override) if override else _SEED_PATH


def _load_seed() -> dict:
    """Return the bundled seed JSON as a fresh dict."""
    with open(_SEED_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _ensure_file_exists(path: Path) -> None:
    """If `path` is missing, materialise it from the seed."""
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(_SEED_PATH, path)


def load_acronyms() -> dict[str, list[str]]:
    """Return a fresh ``{acronym: [expansions...]}`` mapping.

    The returned dict is a deep copy so callers can't accidentally mutate the
    on-disk state.
    """
    path = _store_path()
    with _lock:
        _ensure_file_exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    return deepcopy(data.get("acronyms", {}))


def save_acronyms(acronyms: dict[str, list[str]]) -> None:
    """Replace the stored list atomically."""
    path = _store_path()
    payload = {
        "_comment": (
            "Approved acronyms. Edit via the /settings/acronyms admin page "
            "or directly here. Each entry maps an acronym to one or more "
            "accepted full forms."
        ),
        "acronyms": {k: list(v) for k, v in acronyms.items()},
    }
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def add_acronym(key: str, expansions: list[str]) -> dict[str, list[str]]:
    """Insert or replace one entry. Returns the updated mapping."""
    key = key.strip()
    cleaned = [e.strip() for e in expansions if e.strip()]
    if not key or not cleaned:
        raise ValueError("acronym key and at least one expansion are required")
    acronyms = load_acronyms()
    acronyms[key] = cleaned
    save_acronyms(acronyms)
    return acronyms


def remove_acronym(key: str) -> dict[str, list[str]]:
    """Delete one entry. Idempotent — missing keys are a no-op."""
    acronyms = load_acronyms()
    acronyms.pop(key, None)
    save_acronyms(acronyms)
    return acronyms


def reset_to_seed() -> dict[str, list[str]]:
    """Restore the on-disk store to the bundled seed. Used by tests."""
    seed = _load_seed()
    save_acronyms(seed.get("acronyms", {}))
    return load_acronyms()
