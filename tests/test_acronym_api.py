"""Smoke tests for the acronym admin HTTP endpoints.

Skipped when Flask isn't installed in the test environment (the LLM-only
test runs don't pull the web stack). Run via the project's full requirements
to exercise these.
"""

from __future__ import annotations

from importlib import reload

import pytest

flask = pytest.importorskip("flask")


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Boot the Flask app with auth disabled and the store pointed at tmp."""
    monkeypatch.delenv("APP_PASSWORD", raising=False)  # disable auth gate
    monkeypatch.setenv("ACRONYM_DB_PATH", str(tmp_path / "acronyms.json"))
    # Reload so the store picks up the env override.
    from app.services import acronym_store
    reload(acronym_store)
    from app import main as main_module
    reload(main_module)
    main_module.app.config["TESTING"] = True
    return main_module.app.test_client()


def test_get_lists_seeded_acronyms(client):
    res = client.get("/api/acronyms")
    assert res.status_code == 200
    data = res.get_json()
    assert "LMS" in data["acronyms"]
    assert data["acronyms"]["TEQSA"] == [
        "Tertiary Education Quality and Standards Authority"
    ]


def test_post_adds_an_entry(client):
    res = client.post(
        "/api/acronyms",
        json={"key": "SME", "expansions": ["Subject Matter Expert"]},
    )
    assert res.status_code == 200
    assert res.get_json()["acronyms"]["SME"] == ["Subject Matter Expert"]

    # Round-trip via GET.
    res2 = client.get("/api/acronyms")
    assert "SME" in res2.get_json()["acronyms"]


def test_post_validates_inputs(client):
    res = client.post("/api/acronyms", json={"key": "", "expansions": ["x"]})
    assert res.status_code == 400
    res = client.post("/api/acronyms", json={"key": "FOO", "expansions": []})
    assert res.status_code == 400


def test_post_accepts_string_expansion_for_convenience(client):
    res = client.post(
        "/api/acronyms",
        json={"key": "BIG", "expansions": "Big Important Group"},
    )
    assert res.status_code == 200
    assert res.get_json()["acronyms"]["BIG"] == ["Big Important Group"]


def test_delete_removes_entry(client):
    client.post(
        "/api/acronyms",
        json={"key": "TBD", "expansions": ["To Be Determined"]},
    )
    res = client.delete("/api/acronyms/TBD")
    assert res.status_code == 200
    assert "TBD" not in res.get_json()["acronyms"]


def test_admin_page_renders(client):
    res = client.get("/settings/acronyms")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Approved acronyms" in body
    assert "/api/acronyms" in body


# ── Editor-password gate ──────────────────────────────────────────────────


@pytest.fixture
def gated_client(tmp_path, monkeypatch):
    """Boot the app with the editor-password gate enabled."""
    monkeypatch.delenv("APP_PASSWORD", raising=False)
    monkeypatch.setenv("ACRONYM_DB_PATH", str(tmp_path / "acronyms.json"))
    monkeypatch.setenv("ACRONYM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("SECRET_KEY", "test-key-123")
    from app.services import acronym_store
    reload(acronym_store)
    from app import main as main_module
    reload(main_module)
    main_module.app.config["TESTING"] = True
    return main_module.app.test_client()


def test_gated_page_shows_login_form_when_not_authed(gated_client):
    res = gated_client.get("/settings/acronyms")
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert "Editor sign-in" in body
    # The Add form panel is hidden until login.
    assert 'id="add-form"' not in body


def test_gated_page_shows_editor_after_login(gated_client):
    # Wrong password → 401 with form re-rendered.
    res = gated_client.post(
        "/settings/acronyms/login",
        data={"admin_password": "wrong"},
    )
    assert res.status_code == 401
    assert "Incorrect editor password" in res.get_data(as_text=True)

    # Correct password → redirect, then editor visible.
    res = gated_client.post(
        "/settings/acronyms/login",
        data={"admin_password": "letmein"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    body = res.get_data(as_text=True)
    assert 'id="add-form"' in body
    assert "Editor sign-in" not in body


def test_gated_post_rejected_when_not_authed(gated_client):
    res = gated_client.post(
        "/api/acronyms",
        json={"key": "FOO", "expansions": ["First Of Origin"]},
    )
    assert res.status_code == 403


def test_gated_delete_rejected_when_not_authed(gated_client):
    res = gated_client.delete("/api/acronyms/LMS")
    assert res.status_code == 403


def test_gated_get_still_open_when_not_authed(gated_client):
    """Read-only access stays open so the pipeline can still load the list."""
    res = gated_client.get("/api/acronyms")
    assert res.status_code == 200
    assert "LMS" in res.get_json()["acronyms"]


def test_gated_post_succeeds_after_login(gated_client):
    gated_client.post(
        "/settings/acronyms/login",
        data={"admin_password": "letmein"},
    )
    res = gated_client.post(
        "/api/acronyms",
        json={"key": "FOO", "expansions": ["First Of Origin"]},
    )
    assert res.status_code == 200
    assert "FOO" in res.get_json()["acronyms"]


def test_gated_logout_revokes_editor_session(gated_client):
    gated_client.post(
        "/settings/acronyms/login",
        data={"admin_password": "letmein"},
    )
    gated_client.post("/settings/acronyms/logout")
    res = gated_client.post(
        "/api/acronyms",
        json={"key": "BAR", "expansions": ["Bar Acronym Reach"]},
    )
    assert res.status_code == 403
