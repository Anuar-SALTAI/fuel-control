import pytest

from fuel_control.supabase_client import (
    SupabaseConfigurationError,
    create_supabase_client,
)


def test_missing_configuration_returns_local_fallback():
    assert create_supabase_client({}) is None


def test_required_configuration_has_friendly_error_without_exposing_keys():
    with pytest.raises(
        SupabaseConfigurationError, match="Supabase is not configured"
    ) as error:
        create_supabase_client({}, required=True)
    assert "sb_" not in str(error.value).lower()
