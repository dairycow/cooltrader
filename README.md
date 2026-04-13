# cooltrader

CoolTrader ASX historical data service. Downloads EOD data from CoolTrader, imports CSVs into SQLite, and serves a REST API.

## Setup

```bash
uv sync --all-extras
cp .env.example .env  # then edit with your CoolTrader credentials
```

## Run

```bash
make check    # lint + type-check
uv run cooltrader serve  # starts FastAPI on port 8081
```

## API

- `POST /api/v1/import/download/trigger` - Trigger manual download
- `POST /api/v1/import/download/date` - Download specific date
- `POST /api/v1/import/import/trigger` - Trigger manual import
- `GET /api/v1/import/database/stats` - Database statistics
- `GET /api/v1/import/database/overview` - Symbol overview
- `POST /api/v1/import/schedule/start` - Start scheduler
- `POST /api/v1/import/schedule/stop` - Stop scheduler
- `GET /api/v1/import/schedule/status` - Scheduler status
