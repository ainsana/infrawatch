from datetime import UTC, datetime, timedelta

import pytest

from backend.app.services.host_health import evaluate_host_status


def test_host_status_is_unknown_when_never_seen() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    status = evaluate_host_status(
        last_seen_at=None,
        now=now,
    )

    assert status == "unknown"


def test_host_status_is_online_when_recently_seen() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=2)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
    )

    assert status == "online"


def test_host_status_is_offline_when_last_seen_is_stale() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=10)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
    )

    assert status == "offline"


def test_host_status_is_online_at_exact_threshold() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=5)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
        offline_after=timedelta(minutes=5),
    )

    assert status == "online"


def test_host_status_rejects_invalid_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="Offline threshold must be greater than zero.",
    ):
        evaluate_host_status(
            last_seen_at=None,
            offline_after=timedelta(0),
        )
