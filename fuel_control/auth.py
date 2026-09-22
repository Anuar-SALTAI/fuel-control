"""Supabase authentication and safe Streamlit session handling."""

SESSION_KEYS = (
    "user_id",
    "email",
    "display_name",
    "role",
    "access_token",
    "refresh_token",
)


class AuthManager:
    def __init__(self, client, state):
        self.client = client
        self.state = state

    @property
    def authenticated(self) -> bool:
        return bool(self.state.get("user_id"))

    def _profile(self, user) -> dict:
        response = (
            self.client.table("profiles")
            .select("*")
            .eq("id", user.id)
            .single()
            .execute()
        )
        profile = response.data
        if not profile.get("is_active", True):
            self.logout()
            raise PermissionError("Account is blocked")
        return profile

    def _save(self, session) -> dict:
        profile = self._profile(session.user)
        self.state.update(
            user_id=session.user.id,
            email=session.user.email,
            display_name=profile.get("full_name") or session.user.email,
            role=profile.get("role", "user"),
            access_token=session.access_token,
            refresh_token=session.refresh_token,
        )
        return profile

    def sign_in(self, email: str, password: str) -> dict:
        response = self.client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        return self._save(response.session)

    def sign_up(self, name: str, email: str, password: str):
        if len(password) < 8:
            raise ValueError("Password must contain at least 8 characters")
        response = self.client.auth.sign_up(
            {
                "email": email.strip(),
                "password": password,
                "options": {"data": {"full_name": name.strip()}},
            }
        )
        if response.session:
            self._save(response.session)
            return True
        return False

    def restore(self) -> bool:
        access, refresh = self.state.get("access_token"), self.state.get(
            "refresh_token"
        )
        if not access or not refresh:
            return False
        try:
            response = self.client.auth.set_session(access, refresh)
            self._save(response.session)
            return True
        except Exception:
            self.logout()
            return False

    def logout(self) -> None:
        try:
            self.client.auth.sign_out()
        finally:
            for key in SESSION_KEYS:
                self.state.pop(key, None)
