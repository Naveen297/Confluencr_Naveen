import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

# Amounts are stored in minor units (paise/cents) as integers.
SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL CHECK (length(trim(name)) > 0),
    balance     INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0),
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    seq           INTEGER PRIMARY KEY AUTOINCREMENT,  -- tie-breaker for equal created_at
    id            TEXT NOT NULL UNIQUE,
    account_id    TEXT NOT NULL REFERENCES accounts (id),
    type          TEXT NOT NULL CHECK (type IN ('credit', 'debit')),
    amount        INTEGER NOT NULL CHECK (amount > 0),
    description   TEXT NOT NULL,
    reference_id  TEXT NOT NULL,
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    created_at    TEXT NOT NULL,
    UNIQUE (account_id, reference_id)
);

CREATE INDEX IF NOT EXISTS idx_transactions_history
    ON transactions (account_id, created_at DESC, seq DESC);

CREATE INDEX IF NOT EXISTS idx_transactions_history_by_type
    ON transactions (account_id, type, created_at DESC, seq DESC);

CREATE TRIGGER IF NOT EXISTS transactions_are_immutable_update
BEFORE UPDATE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'transactions are immutable');
END;

CREATE TRIGGER IF NOT EXISTS transactions_are_immutable_delete
BEFORE DELETE ON transactions
BEGIN
    SELECT RAISE(ABORT, 'transactions are immutable');
END;
"""

PathLike = Union[str, Path]


def connect(path: PathLike) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")
    return conn


def init_db(path: PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)
    finally:
        conn.close()


@contextmanager
def write_transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    # IMMEDIATE takes the write lock before the first read, so the balance we
    # check is the balance we update even under concurrent requests.
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
