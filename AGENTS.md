# AGENTS.md - Development Guidelines

## Language
- Use Australian English spelling (e.g., colour, analyse, initialise, organise)
- No emojis in documentation or code

## Build/Lint/Test Commands

```bash
uv sync --all-extras              # Install dependencies
make format                       # Format with ruff
make lint                         # Lint with ruff
make type-check                   # Type check with mypy
make check                        # All checks (lint + type-check)
make test                         # Unit tests only
uv run pytest tests/test_file.py  # Single test file
```

## Code Style

### Formatting & Imports
- Python 3.13+, line length 100 chars
- No inline comments - code should be self-documenting
- Docstrings required for public APIs

```python
# Import order: stdlib -> third-party -> local
import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel, Field

from cooltrader.config import config

if TYPE_CHECKING:
    from cooltrader.database import DatabaseManager
```

### Type Hints
```python
def process_data(items: list[str]) -> dict[str, int]: ...
result: str | None = None
_service: Service | None = None
```

### Naming Conventions
- `PascalCase`: classes (e.g., `DatabaseManager`)
- `snake_case`: functions/variables (e.g., `import_csv`)
- `UPPER_SNAKE_CASE`: constants (e.g., `MAX_RETRIES`)
- `_prefix`: private members (e.g., `_service`)

### Logging
```python
from loguru import logger

logger.info("Message")
logger.error(f"Error: {error}", exc_info=True)
```

## Key Files

| File | Purpose |
|------|---------|
| `cooltrader/config.py` | Pydantic Settings |
| `cooltrader/database.py` | SQLite database manager (peewee) |
| `cooltrader/downloader.py` | CoolTrader CSV downloader |
| `cooltrader/importer.py` | CSV import into database |
| `cooltrader/scheduler.py` | Cron scheduler |
| `cooltrader/api.py` | FastAPI router |
| `cooltrader/main.py` | FastAPI app and lifespan |

## Important Notes

1. Run `make check` before committing
2. Never commit secrets (.env is in .gitignore)
3. Use `TYPE_CHECKING` for circular import avoidance
4. Use `loguru` for all logging
5. Use modern syntax: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
