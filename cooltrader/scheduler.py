"""Unified scheduler service."""

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from cooltrader.config import config
from cooltrader.downloader import create_downloader
from cooltrader.importer import create_importer


class SchedulerService:
    """Unified scheduler for download and import operations."""

    def __init__(self) -> None:
        """Initialize scheduler service."""
        self.scheduler = AsyncIOScheduler(timezone="Australia/Sydney")
        self._running = False
        self._lock = asyncio.Lock()

    async def _trigger_download(self) -> None:
        """Trigger download directly."""
        logger.info("Scheduled download started")
        try:
            downloader = create_downloader()
            filepath = await downloader.download_yesterday()
            await downloader.close()
            logger.info(f"Scheduled download completed: {filepath}")
        except Exception as e:
            logger.error(f"Scheduled download failed: {e}", exc_info=True)

    async def _trigger_import(self) -> None:
        """Trigger import directly."""
        logger.info("Scheduled import started")
        try:
            importer = create_importer(config.historical_data.csv_dir)
            result = importer.import_all()
            logger.info(
                f"Scheduled import completed: "
                f"{result['success']} succeeded, {result['skipped']} skipped, "
                f"{result['errors']} errors, {result['total_bars_imported']} bars"
            )
        except Exception as e:
            logger.error(f"Scheduled import failed: {e}", exc_info=True)

    async def initialize(self) -> None:
        """Register all scheduled jobs."""

        self.scheduler.add_job(
            self._trigger_download,
            trigger=CronTrigger.from_crontab(
                config.cooltrader.download_schedule, timezone="Australia/Sydney"
            ),
            id="download_trigger",
            name="Trigger download",
            replace_existing=True,
        )

        self.scheduler.add_job(
            self._trigger_import,
            trigger=CronTrigger.from_crontab(
                config.cooltrader.import_schedule, timezone="Australia/Sydney"
            ),
            id="import_trigger",
            name="Trigger import",
            replace_existing=True,
        )

        logger.info(
            f"Scheduler initialized: "
            f"download={config.cooltrader.download_schedule}, "
            f"import={config.cooltrader.import_schedule}"
        )

    async def start(self) -> None:
        """Start scheduler."""
        async with self._lock:
            if self._running:
                logger.warning("Scheduler already running")
                return

            self.scheduler.start()
            self._running = True
            logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop scheduler."""
        async with self._lock:
            if not self._running:
                return

            self.scheduler.shutdown(wait=True)
            self._running = False
            logger.info("Scheduler stopped")

    def is_running(self) -> bool:
        """Check if scheduler is running.

        Returns:
            True if running, False otherwise
        """
        return self._running


_scheduler_service: SchedulerService | None = None


async def get_scheduler_service() -> SchedulerService:
    """Get or create scheduler service singleton.

    Returns:
        SchedulerService instance
    """
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
        await _scheduler_service.initialize()
    return _scheduler_service


async def reset_scheduler_service() -> None:
    """Reset scheduler service singleton for test isolation."""
    global _scheduler_service
    if _scheduler_service is not None and _scheduler_service.is_running():
        await _scheduler_service.stop()
    _scheduler_service = None
