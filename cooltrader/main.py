"""CoolTrader data service entry point."""

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import typer
from fastapi import FastAPI
from loguru import logger

from cooltrader.api import health_router, router
from cooltrader.config import config
from cooltrader.database import initialise_database
from cooltrader.scheduler import get_scheduler_service, reset_scheduler_service


def _setup_logging() -> None:
    """Configure logging."""
    log_level = config.logging.level
    logger.remove()

    if config.logging.json_format:
        logger.add(
            sys.stdout,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> | <level>{message}</level>",
        )

    log_path = Path(config.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_path,
        level=log_level,
        rotation=config.logging.rotation,
        retention=config.logging.retention,
        compression="zip",
        serialize=config.logging.json_format,
    )

    logger.info(f"Logging configured at {log_level} level")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.

    Args:
        _app: FastAPI instance

    Yields:
        None
    """
    logger.info("Starting cooltrader service...")

    db_path = initialise_database()
    logger.info(f"Database initialised at {db_path}")

    _setup_logging()

    if config.historical_data.import_enabled:
        scheduler = await get_scheduler_service()
        await scheduler.start()
        logger.info("Scheduler started")

    yield

    await reset_scheduler_service()


app = FastAPI(
    title="cooltrader",
    description="CoolTrader ASX historical data service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

cli = typer.Typer(name="cooltrader", help="CoolTrader ASX historical data service")


@cli.command()
def serve(host: str = "0.0.0.0", port: int = 8081) -> None:
    """Run the CoolTrader service."""
    import uvicorn

    uvicorn.run(
        "cooltrader.main:app",
        host=host,
        port=port,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    cli()
