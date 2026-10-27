import math
import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .database import write_transaction
from .errors import AccountNotFound, DuplicateTransaction, InsufficientFunds, TransactionNotFound
from .money import to_major, to_minor

TX_COLUMNS = "id, account_id, type, amount, description, reference_id, balance_after, created_at"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def new_id() -> str:
    return str(uuid.uuid4())


def serialize_account(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "balance": to_major(row["balance"]),
        "created_at": row["created_at"],
    }


def serialize_transaction(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "account_id": row["account_id"],
        "type": row["type"],
        "amount": to_major(row["amount"]),
        "description": row["description"],
        "reference_id": row["reference_id"],
        "balance_after": to_major(row["balance_after"]),
        "created_at": row["created_at"],
    }


# Accounts

def create_account(conn: sqlite3.Connection, name: str) -> Dict[str, Any]:
    account_id = new_id()
    with write_transaction(conn):
        conn.execute(
            "INSERT INTO accounts (id, name, balance, created_at) VALUES (?, ?, 0, ?)",
            (account_id, name, utc_now()),
        )
    return get_account(conn, account_id)


def fetch_account(conn: sqlite3.Connection, account_id: str) -> sqlite3.Row:
    row = conn.execute(
        "SELECT id, name, balance, created_at FROM accounts WHERE id = ?", (account_id,)
    ).fetchone()
    if row is None:
        raise AccountNotFound(account_id)
    return row


def get_account(conn: sqlite3.Connection, account_id: str) -> Dict[str, Any]:
    return serialize_account(fetch_account(conn, account_id))


def get_account_detail(conn: sqlite3.Connection, account_id: str) -> Dict[str, Any]:
    account = get_account(conn, account_id)
    stats = conn.execute(
        """
        SELECT
            COUNT(*)                                                    AS tx_count,
            COALESCE(SUM(type = 'credit'), 0)                           AS credit_count,
            COALESCE(SUM(type = 'debit'), 0)                            AS debit_count,
            COALESCE(SUM(CASE WHEN type = 'credit' THEN amount END), 0) AS credits,
            COALESCE(SUM(CASE WHEN type = 'debit'  THEN amount END), 0) AS debits,
            MAX(created_at)                                             AS last_at
        FROM transactions
        WHERE account_id = ?
        """,
        (account_id,),
    ).fetchone()
    account["summary"] = {
        "total_credits": to_major(stats["credits"]),
        "total_debits": to_major(stats["debits"]),
        "transaction_count": stats["tx_count"],
        "credit_count": stats["credit_count"],
        "debit_count": stats["debit_count"],
        "last_transaction_at": stats["last_at"],
    }
    return account


def list_accounts(conn: sqlite3.Connection, search: Optional[str] = None) -> List[Dict[str, Any]]:
    sql = "SELECT id, name, balance, created_at FROM accounts"
    params: List[Any] = []
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        sql += " WHERE name LIKE ? ESCAPE '\\' OR id LIKE ? ESCAPE '\\'"
        params += [f"%{escaped}%", f"{escaped}%"]
    sql += " ORDER BY created_at DESC, rowid DESC"
    return [serialize_account(row) for row in conn.execute(sql, params)]


def get_balance(conn: sqlite3.Connection, account_id: str) -> Dict[str, Any]:
    row = fetch_account(conn, account_id)
    return {"account_id": row["id"], "balance": to_major(row["balance"]), "as_of": utc_now()}


# Transactions

def find_by_reference(conn: sqlite3.Connection, account_id: str, reference_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        f"SELECT {TX_COLUMNS} FROM transactions WHERE account_id = ? AND reference_id = ?",
        (account_id, reference_id),
    ).fetchone()


def duplicate_error(existing: sqlite3.Row) -> DuplicateTransaction:
    return DuplicateTransaction(
        f"A transaction with reference_id '{existing['reference_id']}' already exists on this "
        "account. No new transaction was created and the balance is unchanged.",
        {"transaction": serialize_transaction(existing)},
    )


def post_transaction(
    conn: sqlite3.Connection,
    account_id: str,
    *,
    type: str,
    amount: Decimal,
    description: str,
    reference_id: str,
) -> Dict[str, Any]:
    amount_minor = to_minor(amount)

    try:
        with write_transaction(conn):
            account = fetch_account(conn, account_id)

            existing = find_by_reference(conn, account_id, reference_id)
            if existing is not None:
                raise duplicate_error(existing)

            current = account["balance"]
            if type == "debit" and amount_minor > current:
                raise InsufficientFunds(
                    "Insufficient balance. The debit was rejected and the balance is unchanged.",
                    {
                        "balance": to_major(current),
                        "requested": to_major(amount_minor),
                        "shortfall": to_major(amount_minor - current),
                    },
                )

            new_balance = current + amount_minor if type == "credit" else current - amount_minor
            tx_id = new_id()

            conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
            conn.execute(
                f"INSERT INTO transactions ({TX_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (tx_id, account_id, type, amount_minor, description, reference_id, new_balance, utc_now()),
            )
    except sqlite3.IntegrityError:
        # Safety net in case the unique (account_id, reference_id) constraint fires.
        existing = find_by_reference(conn, account_id, reference_id)
        if existing is not None:
            raise duplicate_error(existing) from None
        raise

    return get_transaction(conn, account_id, tx_id)


def get_transaction(conn: sqlite3.Connection, account_id: str, transaction_id: str) -> Dict[str, Any]:
    fetch_account(conn, account_id)
    row = conn.execute(
        f"SELECT {TX_COLUMNS} FROM transactions WHERE id = ? AND account_id = ?",
        (transaction_id, account_id),
    ).fetchone()
    if row is None:
        raise TransactionNotFound(transaction_id)
    return serialize_transaction(row)


def list_transactions(
    conn: sqlite3.Connection,
    account_id: str,
    *,
    type: Optional[str],
    page: int,
    limit: int,
) -> Dict[str, Any]:
    fetch_account(conn, account_id)

    where = "account_id = ?"
    params: List[Any] = [account_id]
    if type is not None:
        where += " AND type = ?"
        params.append(type)

    total = conn.execute(f"SELECT COUNT(*) FROM transactions WHERE {where}", params).fetchone()[0]
    rows = conn.execute(
        f"""
        SELECT {TX_COLUMNS} FROM transactions
        WHERE {where}
        ORDER BY created_at DESC, seq DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, (page - 1) * limit],
    ).fetchall()

    total_pages = math.ceil(total / limit) if total else 0
    return {
        "account_id": account_id,
        "type": type,
        "data": [serialize_transaction(row) for row in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1 and total_pages > 0,
        },
    }
