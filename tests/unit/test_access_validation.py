from app.services.access_validation import (
    AccessStatus,
    check_access,
    check_local_bypass,
    skip_auth_enabled,
    verify_memberpress,
    verify_stripe,
)


def test_skip_auth_enabled_true(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "true")
    assert skip_auth_enabled() is True


def test_skip_auth_enabled_false_by_default(monkeypatch):
    monkeypatch.delenv("SKIP_AUTH", raising=False)
    assert skip_auth_enabled() is False


def test_skip_auth_enabled_rejects_other_values(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "yes")
    assert skip_auth_enabled() is False


def test_local_bypass_grants_access_when_enabled(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "true")
    result = check_local_bypass()
    assert result is not None
    assert result.is_valid
    assert result.access_method == "local_bypass"


def test_local_bypass_returns_none_when_disabled(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "false")
    assert check_local_bypass() is None


def test_memberpress_unavailable_when_unconfigured(monkeypatch):
    monkeypatch.delenv("MEMBERPRESS_BASE_URL", raising=False)
    monkeypatch.delenv("MEMBERPRESS_ENDPOINT", raising=False)
    monkeypatch.delenv("MEMBERPRESS_API_KEY", raising=False)
    result = verify_memberpress({})
    assert result.status == AccessStatus.PROVIDER_UNAVAILABLE
    assert not result.is_valid


def test_stripe_unavailable_when_unconfigured(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    result = verify_stripe({})
    assert result.status == AccessStatus.PROVIDER_UNAVAILABLE
    assert not result.is_valid


def test_check_access_denies_when_nothing_configured(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "false")
    monkeypatch.delenv("MEMBERPRESS_BASE_URL", raising=False)
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    result = check_access({})
    assert not result.is_valid


def test_check_access_grants_when_skip_auth_on(monkeypatch):
    monkeypatch.setenv("SKIP_AUTH", "true")
    result = check_access({})
    assert result.is_valid
