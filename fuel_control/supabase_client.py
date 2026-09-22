"""Supabase client construction from Streamlit Secrets."""


class SupabaseConfigurationError(RuntimeError):
    """Raised when Supabase is explicitly required but not configured."""


def create_supabase_client(secrets, *, required: bool = False):
    """Return an anon-key client, or None for the local SQLite fallback."""
    try:
        url = secrets.get("SUPABASE_URL", "")
        anon_key = secrets.get("SUPABASE_ANON_KEY", "")
    except Exception:
        url = anon_key = ""
    if not url or not anon_key:
        if required:
            raise SupabaseConfigurationError(
                "Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit Secrets."
            )
        return None

    from supabase import create_client

    return create_client(url, anon_key)
