from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class LedgerError(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details


class AccountNotFound(LedgerError):
    status_code = 404
    code = "ACCOUNT_NOT_FOUND"

    def __init__(self, account_id: str):
        super().__init__(f"Account '{account_id}' does not exist.", {"account_id": account_id})


class TransactionNotFound(LedgerError):
    status_code = 404
    code = "TRANSACTION_NOT_FOUND"

    def __init__(self, transaction_id: str):
        super().__init__(
            f"Transaction '{transaction_id}' does not exist on this account.",
            {"transaction_id": transaction_id},
        )


class InsufficientFunds(LedgerError):
    status_code = 422
    code = "INSUFFICIENT_FUNDS"


class DuplicateTransaction(LedgerError):
    status_code = 409
    code = "DUPLICATE_TRANSACTION"


HTTP_ERROR_CODES = {
    400: "BAD_REQUEST",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


def error_body(code: str, message: str, details: Any = None) -> Dict[str, Any]:
    body: Dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        body["details"] = details
    return {"error": body}


def _validation_message(raw: str) -> str:
    prefix = "Value error, "
    return raw[len(prefix):] if raw.startswith(prefix) else raw


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(LedgerError)
    async def handle_ledger_error(_: Request, exc: LedgerError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = []
        for err in exc.errors():
            loc = [str(part) for part in err.get("loc", ()) if part != "body"]
            fields.append(
                {
                    "field": ".".join(loc) or "body",
                    "message": _validation_message(err.get("msg", "Invalid value")),
                }
            )
        summary = fields[0]["message"] if len(fields) == 1 else "Some fields are invalid."
        return JSONResponse(status_code=422, content=error_body("VALIDATION_ERROR", summary, fields))

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(code, message),
            headers=getattr(exc, "headers", None),
        )
