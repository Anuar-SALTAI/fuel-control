"""Creation of the Supabase client from Streamlit secrets."""

from collections.abc import Mapping


def create_supabase_client(secrets: Mapping[str, str]):
    """Return a configured client, or ``None`` for the local SQLite fallback."""
    url = secrets.get("SUPABASE_URL")
    key = secrets.get("SUPABASE_ANON_KEY")
    if not url or not key:
        return None

    from supabase import create_client

    return create_client(url, key)
