import sqlite3
from typing import Iterator, Optional

from fastapi import APIRouter, Depends, Query, Request, status

from .. import ledger
from ..config import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ..database import connect
from ..schemas import (
    Account,
    AccountCreate,
    AccountDetail,
    AccountList,
    Balance,
    Transaction,
    TransactionCreate,
    TransactionPage,
    TransactionType,
)

router = APIRouter(prefix="/api")


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


ERROR_RESPONSE = {"description": "Error envelope: {error: {code, message, details}}"}
NOT_FOUND = {404: {**ERROR_RESPONSE, "description": "Account not found"}}


@router.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@router.post(
    "/accounts",
    response_model=Account,
    status_code=status.HTTP_201_CREATED,
    tags=["accounts"],
    responses={422: {**ERROR_RESPONSE, "description": "Missing name, or a client-supplied balance"}},
)
def create_account(payload: AccountCreate, db: sqlite3.Connection = Depends(get_db)):
    """Open a new account. The balance always starts at 0."""
    return ledger.create_account(db, payload.name)


@router.get("/accounts", response_model=AccountList, tags=["accounts"])
def list_accounts(
    search: Optional[str] = Query(None, max_length=100, description="Match on name or id prefix"),
    db: sqlite3.Connection = Depends(get_db),
):
    accounts = ledger.list_accounts(db, search.strip() if search else None)
    return {"data": accounts, "total_records": len(accounts)}


@router.get(
    "/accounts/{account_id}",
    response_model=AccountDetail,
    tags=["accounts"],
    responses=NOT_FOUND,
)
def get_account(account_id: str, db: sqlite3.Connection = Depends(get_db)):
    """Account details plus running totals."""
    return ledger.get_account_detail(db, account_id)


@router.get(
    "/accounts/{account_id}/balance",
    response_model=Balance,
    tags=["accounts"],
    responses=NOT_FOUND,
)
def get_balance(account_id: str, db: sqlite3.Connection = Depends(get_db)):
    return ledger.get_balance(db, account_id)


@router.post(
    "/accounts/{account_id}/transactions",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    tags=["transactions"],
    responses={
        **NOT_FOUND,
        409: {**ERROR_RESPONSE, "description": "reference_id already used on this account"},
        422: {**ERROR_RESPONSE, "description": "Invalid input, or insufficient balance for a debit"},
    },
)
def add_transaction(
    account_id: str,
    payload: TransactionCreate,
    db: sqlite3.Connection = Depends(get_db),
):
    """Post a credit or debit. A repeated reference_id on the same account returns 409."""
    return ledger.post_transaction(
        db,
        account_id,
        type=payload.type,
        amount=payload.amount,
        description=payload.description,
        reference_id=payload.reference_id,
    )


@router.get(
    "/accounts/{account_id}/transactions",
    response_model=TransactionPage,
    tags=["transactions"],
    responses=NOT_FOUND,
)
def list_transactions(
    account_id: str,
    type: Optional[TransactionType] = Query(None, description="credit or debit. Omit for both."),
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: sqlite3.Connection = Depends(get_db),
):
    """Transaction history, newest first."""
    return ledger.list_transactions(db, account_id, type=type, page=page, limit=limit)


@router.get(
    "/accounts/{account_id}/transactions/{transaction_id}",
    response_model=Transaction,
    tags=["transactions"],
    responses={404: {**ERROR_RESPONSE, "description": "Account or transaction not found"}},
)
def get_transaction(
    account_id: str, transaction_id: str, db: sqlite3.Connection = Depends(get_db)
):
    return ledger.get_transaction(db, account_id, transaction_id)
