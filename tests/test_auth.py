from types import SimpleNamespace

from fuel_control.auth import AuthService


class FakeAuth:
    def __init__(self):
        self.calls = []
        self.session = None

    def sign_in_with_password(self, credentials):
        self.calls.append(("login", credentials))
        user = SimpleNamespace(id="user-a", email=credentials["email"])
        self.session = SimpleNamespace(user=user)
        return SimpleNamespace(user=user, session=self.session)

    def sign_up(self, credentials):
        self.calls.append(("register", credentials))
        return SimpleNamespace(user=SimpleNamespace(id="pending"), session=None)

    def get_session(self):
        return self.session

    def sign_out(self):
        self.calls.append(("logout", None))
        self.session = None


def test_login_and_logout_session():
    backend = FakeAuth()
    service = AuthService(SimpleNamespace(auth=backend))

    outcome = service.login(" driver@example.com ", "secret")
    assert outcome.user.id == "user-a"
    assert service.current_user().id == "user-a"
    assert backend.calls[0][1]["email"] == "driver@example.com"

    service.logout()
    assert service.current_user() is None
    assert backend.calls[-1][0] == "logout"


def test_registration_reports_email_confirmation_requirement():
    backend = FakeAuth()
    outcome = AuthService(SimpleNamespace(auth=backend)).register(
        "new@example.com", "secret"
    )
    assert outcome.confirmation_required is True
    assert outcome.session is None
