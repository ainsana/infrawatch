import asyncio
from threading import Event
from unittest.mock import AsyncMock, call, patch

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.monitoring import run_monitoring_cycle
from backend.app.services.scheduler import run_monitoring_scheduler


def test_monitoring_scheduler_runs_cycle_after_interval() -> None:
    async def scenario() -> None:
        with (
            patch(
                "backend.app.services.scheduler.asyncio.sleep",
                new_callable=AsyncMock,
                side_effect=[
                    None,
                    asyncio.CancelledError,
                ],
            ) as mock_sleep,
            patch(
                "backend.app.services.scheduler.asyncio.to_thread",
                new_callable=AsyncMock,
                return_value=1,
            ) as mock_to_thread,
        ):
            with pytest.raises(asyncio.CancelledError):
                await run_monitoring_scheduler(
                    interval_seconds=30,
                )

        assert mock_sleep.await_args_list == [
            call(30),
            call(30),
        ]

        mock_to_thread.assert_awaited_once_with(
            run_monitoring_cycle,
        )

    asyncio.run(scenario())


def test_app_lifespan_starts_and_stops_monitoring_scheduler() -> None:
    started = Event()
    stopped = Event()
    received_intervals: list[int] = []

    async def fake_scheduler(
        interval_seconds: int,
    ) -> None:
        received_intervals.append(interval_seconds)
        started.set()

        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            stopped.set()
            raise

    with (
        patch(
            "backend.app.main.get_settings",
        ) as mock_get_settings,
        patch(
            "backend.app.main.run_monitoring_scheduler",
            new=fake_scheduler,
        ),
    ):
        mock_get_settings.return_value.monitoring_interval_seconds = 30

        with TestClient(app):
            assert started.wait(timeout=2)

        assert stopped.wait(timeout=2)

    assert received_intervals == [30]
