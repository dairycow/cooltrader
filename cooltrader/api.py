"""FastAPI endpoints for historical data management."""

from datetime import date, datetime
from typing import cast

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from cooltrader.config import config
from cooltrader.database import get_database_manager
from cooltrader.downloader import create_downloader
from cooltrader.importer import create_importer

router = APIRouter(prefix="/import", tags=["historical-data"])


class JobTriggerResponse(BaseModel):
    """Response model for job trigger endpoints."""

    message: str


class DatabaseStatsResponse(BaseModel):
    """Response model for database stats."""

    db_path: str
    db_size_bytes: int
    db_size_mb: float
    total_symbols: int
    total_bars: int


class DatabaseOverviewResponse(BaseModel):
    """Response model for database overview."""

    total_symbols: int
    symbols: list[dict[str, str | int | None]]


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""

    enabled: bool
    running: bool
    download_schedule: str
    import_schedule: str
    timezone: str


@router.post("/download/trigger", response_model=JobTriggerResponse)
async def trigger_download() -> JobTriggerResponse:
    """Trigger manual CoolTrader download."""
    if not config.historical_data.import_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Import is disabled in configuration",
        )

    downloader = create_downloader()
    try:
        filepath = await downloader.download_yesterday()
        await downloader.close()
        return JobTriggerResponse(
            message=f"Download completed: {filepath}"
            if filepath
            else "Download skipped: no file available"
        )
    except Exception as e:
        await downloader.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {e}",
        ) from None


class DownloadDateRequest(BaseModel):
    """Request model for manual date download."""

    date: str


@router.post("/download/date", response_model=JobTriggerResponse)
async def download_specific_date(request: DownloadDateRequest) -> JobTriggerResponse:
    """Manually download CSV for specific date."""
    try:
        datetime.strptime(request.date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        ) from None

    if not config.historical_data.import_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Import is disabled in configuration",
        )

    downloader = create_downloader()
    try:
        target_date = date.fromisoformat(request.date)
        filepath = await downloader.download_csv(target_date)
        await downloader.close()
        return JobTriggerResponse(message=f"Download completed: {filepath}")
    except Exception as e:
        await downloader.close()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {e}",
        ) from None


@router.post("/import/trigger", response_model=JobTriggerResponse)
async def trigger_import() -> JobTriggerResponse:
    """Trigger manual CSV import."""
    if not config.historical_data.import_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Import is disabled in configuration",
        )

    try:
        importer = create_importer(config.historical_data.csv_dir)
        result = importer.import_all()
        return JobTriggerResponse(
            message=f"Import completed: {result['success']} succeeded, "
            f"{result['skipped']} skipped, {result['errors']} errors, "
            f"{result['total_bars_imported']} bars"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {e}",
        ) from None


@router.post("/schedule/start", response_model=SchedulerStatusResponse)
async def start_scheduler() -> SchedulerStatusResponse:
    """Start scheduled downloads and imports."""
    if not config.historical_data.import_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Import is disabled in configuration",
        )

    from cooltrader.scheduler import get_scheduler_service

    scheduler = await get_scheduler_service()

    if scheduler.is_running():
        return SchedulerStatusResponse(
            enabled=config.historical_data.import_enabled,
            running=True,
            download_schedule=config.cooltrader.download_schedule,
            import_schedule=config.cooltrader.import_schedule,
            timezone="Australia/Sydney",
        )

    await scheduler.start()

    return SchedulerStatusResponse(
        enabled=config.historical_data.import_enabled,
        running=True,
        download_schedule=config.cooltrader.download_schedule,
        import_schedule=config.cooltrader.import_schedule,
        timezone="Australia/Sydney",
    )


@router.post("/schedule/stop", response_model=SchedulerStatusResponse)
async def stop_scheduler() -> SchedulerStatusResponse:
    """Stop scheduled downloads and imports."""
    from cooltrader.scheduler import get_scheduler_service

    scheduler = await get_scheduler_service()

    if not scheduler.is_running():
        return SchedulerStatusResponse(
            enabled=config.historical_data.import_enabled,
            running=False,
            download_schedule=config.cooltrader.download_schedule,
            import_schedule=config.cooltrader.import_schedule,
            timezone="Australia/Sydney",
        )

    await scheduler.stop()

    return SchedulerStatusResponse(
        enabled=config.historical_data.import_enabled,
        running=False,
        download_schedule=config.cooltrader.download_schedule,
        import_schedule=config.cooltrader.import_schedule,
        timezone="Australia/Sydney",
    )


@router.get("/schedule/status", response_model=SchedulerStatusResponse)
async def schedule_status() -> SchedulerStatusResponse:
    """Get scheduler status."""
    from cooltrader.scheduler import get_scheduler_service

    scheduler = await get_scheduler_service()

    return SchedulerStatusResponse(
        enabled=config.historical_data.import_enabled,
        running=scheduler.is_running(),
        download_schedule=config.cooltrader.download_schedule,
        import_schedule=config.cooltrader.import_schedule,
        timezone="Australia/Sydney",
    )


@router.get("/database/stats", response_model=DatabaseStatsResponse)
async def get_database_stats_endpoint() -> DatabaseStatsResponse:
    """Get database statistics."""
    db_manager = get_database_manager()
    stats = db_manager.get_database_stats()

    return DatabaseStatsResponse(
        db_path=cast(str, stats["db_path"]),
        db_size_bytes=cast(int, stats["db_size_bytes"]),
        db_size_mb=cast(float, stats["db_size_mb"]),
        total_symbols=cast(int, stats["total_symbols"]),
        total_bars=cast(int, stats["total_bars"]),
    )


@router.get("/database/overview", response_model=DatabaseOverviewResponse)
async def get_database_overview_endpoint() -> DatabaseOverviewResponse:
    """Get database overview."""
    db_manager = get_database_manager()
    overview = db_manager.get_database_overview()

    return DatabaseOverviewResponse(
        total_symbols=cast(int, overview["total_symbols"]),
        symbols=cast(list[dict[str, str | int | None]], overview["symbols"]),
    )
