from decimal import Decimal
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config import MAX_TRANSACTION_AMOUNT

TransactionType = Literal["credit", "debit"]


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AccountCreate(StrictInput):
    name: str = Field(min_length=1, max_length=100, examples=["Asha Raman"])

    @model_validator(mode="before")
    @classmethod
    def reject_client_balance(cls, data: Any) -> Any:
        if isinstance(data, dict) and "balance" in data:
            raise ValueError("balance cannot be set by the client. New accounts always open at 0.")
        return data


class Account(BaseModel):
    id: str
    name: str
    balance: float
    created_at: str


class AccountSummary(BaseModel):
    total_credits: float
    total_debits: float
    transaction_count: int
    credit_count: int
    debit_count: int
    last_transaction_at: Optional[str] = None


class AccountDetail(Account):
    summary: AccountSummary


class AccountList(BaseModel):
    data: List[Account]
    total_records: int


class Balance(BaseModel):
    account_id: str
    balance: float
    as_of: str


class TransactionCreate(StrictInput):
    type: TransactionType
    amount: Decimal = Field(
        gt=0,
        le=MAX_TRANSACTION_AMOUNT,
        decimal_places=2,
        examples=["50.00"],
        description="Positive amount with at most two decimal places.",
    )
    description: str = Field(min_length=1, max_length=255, examples=["Salary for October"])
    reference_id: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:\-]*$",
        examples=["INV-2026-0042"],
        description="Unique per account. Letters, digits and . _ : - only.",
    )

    @field_validator("type", mode="before")
    @classmethod
    def normalise_type(cls, value: Any) -> Any:
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("amount", mode="before")
    @classmethod
    def reject_booleans(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError("amount must be a number")
        return value


class Transaction(BaseModel):
    id: str
    account_id: str
    type: TransactionType
    amount: float
    description: str
    reference_id: str
    balance_after: float
    created_at: str


class Pagination(BaseModel):
    page: int
    limit: int
    total_records: int
    total_pages: int
    has_next: bool
    has_previous: bool


class TransactionPage(BaseModel):
    account_id: str
    type: Optional[TransactionType] = None
    data: List[Transaction]
    pagination: Pagination
