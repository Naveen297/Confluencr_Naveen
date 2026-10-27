import sqlite3
import threading
from decimal import Decimal

import pytest

from app import ledger
from app.database import connect
from app.errors import DuplicateTransaction, InsufficientFunds


def test_balance_matches_example_from_brief(client, account, post):
    post(account["id"], "credit", 100)
    post(account["id"], "credit", 50)
    post(account["id"], "debit", 30)
    post(account["id"], "debit", 20)

    assert client.get(f"/api/accounts/{account['id']}/balance").json()["balance"] == 100


def test_balance_always_equals_sum_of_transactions(client, account, post, db_path):
    amounts = [("credit", 500), ("debit", 120.5), ("debit", 1000), ("credit", 0.75),
               ("debit", 380.25), ("debit", 1), ("credit", 42)]
    for type_, amount in amounts:
        post(account["id"], type_, amount)  # the 1000 and 1 debits get rejected

    conn = connect(db_path)
    stored, computed = conn.execute(
        """
        SELECT a.balance,
               COALESCE(SUM(CASE t.type WHEN 'credit' THEN t.amount ELSE -t.amount END), 0)
        FROM accounts a LEFT JOIN transactions t ON t.account_id = a.id
        WHERE a.id = ?
        GROUP BY a.id
        """,
        (account["id"],),
    ).fetchone()
    conn.close()

    assert stored == computed
    assert client.get(f"/api/accounts/{account['id']}/balance").json()["balance"] == 42


def test_running_balance_recorded_on_each_entry(client, account, post):
    post(account["id"], "credit", 100)
    post(account["id"], "debit", 30)
    post(account["id"], "credit", 5)

    data = client.get(f"/api/accounts/{account['id']}/transactions").json()["data"]

    assert [t["balance_after"] for t in data] == [75, 70, 100]


@pytest.mark.parametrize("method", ["put", "patch", "delete"])
def test_api_offers_no_way_to_modify_transactions(client, account, post, method):
    tx = post(account["id"], "credit", 100).json()
    url = f"/api/accounts/{account['id']}/transactions/{tx['id']}"

    res = client.request(method.upper(), url, json={"amount": 1})

    assert res.status_code == 405
    assert client.get(url).json() == tx


def test_database_rejects_updates_and_deletes(account, post, db_path):
    tx = post(account["id"], "credit", 100).json()
    conn = connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute("UPDATE transactions SET amount = 1 WHERE id = ?", (tx["id"],))
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            conn.execute("DELETE FROM transactions WHERE id = ?", (tx["id"],))
    finally:
        conn.close()


def test_database_rejects_negative_balance(account, db_path):
    conn = connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE accounts SET balance = -1 WHERE id = ?", (account["id"],))
    finally:
        conn.close()


def _run_concurrently(db_path, n, work):
    results = []
    lock = threading.Lock()
    barrier = threading.Barrier(n)

    def worker(i):
        conn = connect(db_path)
        try:
            barrier.wait()
            try:
                work(conn, i)
                outcome = "ok"
            except (InsufficientFunds, DuplicateTransaction) as exc:
                outcome = type(exc).__name__
        finally:
            conn.close()
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_concurrent_debits_never_overdraw(client, account, post, db_path):
    post(account["id"], "credit", 100)

    def debit(conn, i):
        ledger.post_transaction(
            conn, account["id"], type="debit", amount=Decimal("10"),
            description="race", reference_id=f"RACE-{i}",
        )

    results = _run_concurrently(db_path, 25, debit)

    assert results.count("ok") == 10
    assert results.count("InsufficientFunds") == 15
    assert client.get(f"/api/accounts/{account['id']}/balance").json()["balance"] == 0


def test_concurrent_duplicates_create_one_transaction(client, account, db_path):
    def credit(conn, _):
        ledger.post_transaction(
            conn, account["id"], type="credit", amount=Decimal("10"),
            description="retry storm", reference_id="SAME-REF",
        )

    results = _run_concurrently(db_path, 20, credit)

    assert results.count("ok") == 1
    assert results.count("DuplicateTransaction") == 19
    assert client.get(f"/api/accounts/{account['id']}/balance").json()["balance"] == 10
