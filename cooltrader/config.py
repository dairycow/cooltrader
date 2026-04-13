"""Configuration management using Pydantic Settings v2."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABASE_")

    path: str = Field(
        default="/home/hf/cooltrader/data/cooltrader.db", description="SQLite database path"
    )


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    file: str = Field(
        default="/home/hf/cooltrader/logs/cooltrader.log", description="Log file path"
    )
    rotation: str = Field(default="100 MB", description="Log rotation size")
    retention: str = Field(default="7 days", description="Log retention period")
    json_format: bool = Field(default=True, description="Use JSON log format")


class HistoricalDataConfig(BaseSettings):
    """Historical data configuration."""

    csv_dir: str = Field(default="/home/hf/cooltrader/data/raw", description="CSV data directory")
    import_enabled: bool = Field(default=True, description="Enable data import")


class CoolTraderConfig(BaseSettings):
    """CoolTrader data provider configuration."""

    username: str = Field(default="", description="CoolTrader username")
    password: str = Field(default="", description="CoolTrader password")
    base_url: str = Field(
        default="https://data.cooltrader.com.au", description="CoolTrader API base URL"
    )
    download_schedule: str = Field(default="55 9 * * *", description="Download cron schedule")
    import_schedule: str = Field(default="5 10 * * *", description="Import cron schedule")


class Config(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    historical_data: HistoricalDataConfig = Field(default_factory=HistoricalDataConfig)
    cooltrader: CoolTraderConfig = Field(default_factory=CoolTraderConfig)

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()


config: Config = Config.load()
