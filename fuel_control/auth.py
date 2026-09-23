"""Small, testable facade around Supabase Auth."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthOutcome:
    user: object | None
    session: object | None
    confirmation_required: bool = False


class AuthService:
    def __init__(self, client):
        self.client = client

    def login(self, email: str, password: str) -> AuthOutcome:
        response = self.client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        return AuthOutcome(response.user, response.session)

    def register(self, email: str, password: str) -> AuthOutcome:
        response = self.client.auth.sign_up(
            {"email": email.strip(), "password": password}
        )
        return AuthOutcome(
            response.user,
            response.session,
            confirmation_required=response.user is not None and response.session is None,
        )

    def current_user(self):
        session = self.client.auth.get_session()
        return session.user if session else None

    def logout(self) -> None:
        self.client.auth.sign_out()
