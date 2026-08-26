import asyncio
import logging

from backend.app.services.monitoring import run_monitoring_cycle

logger = logging.getLogger(__name__)


async def run_monitoring_scheduler(
    interval_seconds: int,
) -> None:
    logger.info(
        "Monitoring scheduler started: interval_seconds=%s",
        interval_seconds,
    )

    try:
        while True:
            await asyncio.sleep(interval_seconds)

            try:
                executed_count = await asyncio.to_thread(
                    run_monitoring_cycle,
                )
            except Exception:
                logger.exception(
                    "Monitoring cycle failed.",
                )
                continue

            logger.info(
                "Monitoring cycle completed: executed_monitors=%s",
                executed_count,
            )
    finally:
        logger.info(
            "Monitoring scheduler stopped.",
        )
