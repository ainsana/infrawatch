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


def test_monitoring_interval_seconds_defaults_to_60() -> None:
    settings = Settings(
        postgres_password="test-password",
        _env_file=None,
    )

    assert settings.monitoring_interval_seconds == 60


def test_monitoring_interval_seconds_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        Settings(
            postgres_password="test-password",
            monitoring_interval_seconds=0,
            _env_file=None,
        )
