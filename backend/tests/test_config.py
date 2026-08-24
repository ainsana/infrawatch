import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_host_offline_after_seconds_defaults_to_300() -> None:
    settings = Settings(
        postgres_password="test-password",
        _env_file=None,
    )

    assert settings.host_offline_after_seconds == 300


def test_host_offline_after_seconds_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(
            postgres_password="test-password",
            host_offline_after_seconds=0,
            _env_file=None,
        )
