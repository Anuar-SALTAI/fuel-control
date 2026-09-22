from types import SimpleNamespace

import pytest

from fuel_control.auth import AuthManager


class Query:
    def __init__(self, data):
        self.data = data

    def select(self, *_):
        return self

    def eq(self, *_):
        return self

    def single(self):
        return self

    def execute(self):
        return SimpleNamespace(data=self.data)


class FakeAuth:
    def __init__(self):
        self.signed_out = False

    def sign_in_with_password(self, credentials):
        assert "password" in credentials
        user = SimpleNamespace(id="user-a", email=credentials["email"])
        return SimpleNamespace(
            session=SimpleNamespace(
                user=user, access_token="access", refresh_token="refresh"
            )
        )

    def set_session(self, access, refresh):
        return self.sign_in_with_password(
            {"email": "a@example.com", "password": "unused"}
        )

    def sign_up(self, payload):
        return SimpleNamespace(user=payload["email"], session=None)

    def sign_out(self):
        self.signed_out = True


class FakeClient:
    def __init__(self, profile=None):
        self.auth = FakeAuth()
        self.profile = profile or {
            "id": "user-a",
            "full_name": "A",
            "role": "user",
            "is_active": True,
        }

    def table(self, name):
        assert name == "profiles"
        return Query(self.profile)


def test_login_restore_and_logout_state_never_contains_password():
    state = {}
    manager = AuthManager(FakeClient(), state)
    manager.sign_in("a@example.com", "secret-password")
    assert state["user_id"] == "user-a"
    assert state["email"] == "a@example.com"
    assert state["display_name"] == "A"
    assert state["role"] == "user"
    assert "password" not in state
    assert manager.restore()
    manager.logout()
    assert not manager.authenticated


def test_signup_rejects_short_password():
    with pytest.raises(ValueError):
        AuthManager(FakeClient(), {}).sign_up("A", "a@example.com", "short")


def test_registration_with_confirmation_does_not_create_local_session():
    state = {}
    assert (
        AuthManager(FakeClient(), state).sign_up("A", "a@example.com", "long-password")
        is False
    )
    assert "user_id" not in state


def test_registration_without_confirmation_signs_user_in():
    client = FakeClient()
    session = client.auth.sign_in_with_password(
        {"email": "a@example.com", "password": "long-password"}
    ).session
    client.auth.sign_up = lambda _payload: SimpleNamespace(session=session)
    state = {}
    assert AuthManager(client, state).sign_up("A", "a@example.com", "long-password")
    assert state["user_id"] == "user-a"


def test_login_failure_leaves_session_empty():
    client = FakeClient()

    def fail(_credentials):
        raise ValueError("invalid credentials")

    client.auth.sign_in_with_password = fail
    state = {}
    with pytest.raises(ValueError):
        AuthManager(client, state).sign_in("a@example.com", "wrong-password")
    assert state == {}


def test_blocked_profile_cannot_login():
    profile = {"id": "user-a", "full_name": "A", "role": "user", "is_active": False}
    with pytest.raises(PermissionError):
        AuthManager(FakeClient(profile), {}).sign_in("a@example.com", "long-password")


def test_missing_supabase_secrets_uses_sqlite_fallback(monkeypatch):
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

    monkeypatch.delenv("FUEL_CONTROL_LOCAL", raising=False)
    app = AppTest.from_file("app.py", default_timeout=15).run()
    assert not list(app.exception)
    assert app.sidebar.radio
    assert any(button.label == "Жазбаны сақтау" for button in app.button)
