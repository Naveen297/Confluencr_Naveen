import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATABASE_PATH = Path(os.environ.get("LEDGER_DB_PATH", PROJECT_ROOT / "data" / "ledger.db"))
FRONTEND_DIST = Path(os.environ.get("LEDGER_FRONTEND_DIST", PROJECT_ROOT / "frontend" / "dist"))

MAX_TRANSACTION_AMOUNT = 1_000_000_000

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100
