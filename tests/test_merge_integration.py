from pathlib import Path

from fuel_control.i18n import TEXT


def test_latest_ui_and_supabase_auth_are_integrated():
    app = Path("app.py").read_text(encoding="utf-8")
    assert 'HERO_BANNER = ASSETS_DIR / "hero_banner.png"' in app
    assert 'SIDEBAR_PHOTO = ASSETS_DIR / "sidebar_photo.png"' in app
    assert "parse_numeric_input" in app
    assert "AuthManager" in app
    assert "SupabaseRepository" in app
    assert "create_supabase_client" in app


def test_merged_localization_keeps_ui_and_auth_terms():
    assert TEXT["kk"]["start_odometer"] == "Бастапқы жүріс, км"
    assert TEXT["kk"]["end_odometer"] == "Соңғы жүріс, км"
    assert TEXT["kk"]["login"] == "Кіру"
    assert TEXT["kk"]["register"] == "Тіркелу"
    assert TEXT["ru"]["login"] == "Войти"
    assert TEXT["ru"]["register"] == "Регистрация"


def test_merged_requirements_and_secret_ignores_are_preserved():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    for dependency in ("streamlit", "pandas", "openpyxl", "supabase"):
        assert dependency in requirements
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    assert ".streamlit/secrets.toml" in ignored
    assert ".env" in ignored


def test_conflicted_text_files_have_no_merge_markers():
    for path in (".gitignore", "README.md", "app.py", "fuel_control/i18n.py", "requirements.txt"):
        content = Path(path).read_text(encoding="utf-8")
        assert "<<<<<<<" not in content
        assert ">>>>>>>" not in content
