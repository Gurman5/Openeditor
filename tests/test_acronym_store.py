"""Tests for the acronym JSON-file store."""

from __future__ import annotations

import json
from importlib import reload

import pytest


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    """Point the store at a temp file so tests don't mutate the seed."""
    db_path = tmp_path / "acronyms.json"
    monkeypatch.setenv("ACRONYM_DB_PATH", str(db_path))
    # Reload to pick up the env var inside the module's _store_path() helper.
    from app.services import acronym_store as mod
    reload(mod)
    yield mod, db_path


def test_first_load_seeds_from_bundled_file(isolated_store):
    mod, db_path = isolated_store
    assert not db_path.exists()
    acronyms = mod.load_acronyms()
    # Seed contains all 17 entries the client provided.
    assert "LMS" in acronyms
    assert "TEQSA" in acronyms
    assert "GenAI" in acronyms
    assert acronyms["HDR"] == [
        "Higher Degree by Research",
        "Research by Higher Degree",
    ]
    # File has been materialised on disk.
    assert db_path.exists()


def test_save_writes_atomically_and_round_trips(isolated_store):
    mod, db_path = isolated_store
    mod.load_acronyms()  # seed
    new_value = {"FOO": ["First Of Origin"]}
    mod.save_acronyms(new_value)
    assert mod.load_acronyms() == new_value
    on_disk = json.loads(db_path.read_text(encoding="utf-8"))
    assert on_disk["acronyms"] == new_value


def test_add_acronym_inserts_and_returns_full_map(isolated_store):
    mod, _ = isolated_store
    updated = mod.add_acronym("SME", ["Subject Matter Expert"])
    assert updated["SME"] == ["Subject Matter Expert"]
    assert updated["LMS"] == ["learning management system"]


def test_add_acronym_validates_inputs(isolated_store):
    mod, _ = isolated_store
    with pytest.raises(ValueError):
        mod.add_acronym("", ["something"])
    with pytest.raises(ValueError):
        mod.add_acronym("XYZ", [])
    with pytest.raises(ValueError):
        mod.add_acronym("XYZ", [""])


def test_remove_acronym_is_idempotent(isolated_store):
    mod, _ = isolated_store
    mod.load_acronyms()
    after_first = mod.remove_acronym("LMS")
    assert "LMS" not in after_first
    after_second = mod.remove_acronym("LMS")
    assert after_second == after_first


def test_load_returns_deep_copy(isolated_store):
    mod, _ = isolated_store
    a = mod.load_acronyms()
    a["LMS"].append("MUTATED")
    b = mod.load_acronyms()
    assert "MUTATED" not in b["LMS"]
