import asyncio

from backend.app.services.monitoring import run_monitoring_cycle


async def run_monitoring_scheduler(
    interval_seconds: int,
) -> None:
    while True:
        await asyncio.sleep(interval_seconds)

        await asyncio.to_thread(
            run_monitoring_cycle,
        )
