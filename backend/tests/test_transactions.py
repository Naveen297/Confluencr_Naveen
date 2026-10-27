import pytest


def balance_of(client, account_id):
    return client.get(f"/api/accounts/{account_id}/balance").json()["balance"]


def test_credit_increases_balance(client, account, post):
    post(account["id"], "credit", 100)
    res = post(account["id"], "credit", 50)

    assert res.status_code == 201
    assert balance_of(client, account["id"]) == 150


def test_transaction_has_all_fields(account, post):
    res = post(account["id"], "credit", 75.25, reference_id="INV-1", description="Invoice 1")
    tx = res.json()

    for field in ["id", "account_id", "type", "amount", "description", "reference_id", "created_at"]:
        assert field in tx
    assert tx["account_id"] == account["id"]
    assert tx["type"] == "credit"
    assert tx["amount"] == 75.25
    assert tx["description"] == "Invoice 1"
    assert tx["reference_id"] == "INV-1"
    assert tx["balance_after"] == 75.25


def test_debit_decreases_balance(client, account, post):
    post(account["id"], "credit", 100)
    res = post(account["id"], "debit", 30)

    assert res.status_code == 201
    assert balance_of(client, account["id"]) == 70


def test_debit_with_insufficient_balance_is_rejected(client, account, post):
    post(account["id"], "credit", 100)

    res = post(account["id"], "debit", 150)

    assert res.status_code == 422
    error = res.json()["error"]
    assert error["code"] == "INSUFFICIENT_FUNDS"
    assert error["details"] == {"balance": 100, "requested": 150, "shortfall": 50}
    assert balance_of(client, account["id"]) == 100

    history = client.get(f"/api/accounts/{account['id']}/transactions").json()
    assert history["pagination"]["total_records"] == 1


def test_debit_of_exact_balance_is_allowed(client, account, post):
    post(account["id"], "credit", 100)
    assert post(account["id"], "debit", 100).status_code == 201
    assert balance_of(client, account["id"]) == 0


def test_debit_on_empty_account_is_rejected(client, account, post):
    assert post(account["id"], "debit", 0.01).status_code == 422
    assert balance_of(client, account["id"]) == 0


def test_duplicate_reference_is_not_created_again(client, account, post):
    first = post(account["id"], "credit", 100, reference_id="PAY-1")
    assert first.status_code == 201

    again = post(account["id"], "credit", 100, reference_id="PAY-1")

    assert again.status_code == 409
    error = again.json()["error"]
    assert error["code"] == "DUPLICATE_TRANSACTION"
    assert error["details"]["transaction"]["id"] == first.json()["id"]
    assert balance_of(client, account["id"]) == 100
    history = client.get(f"/api/accounts/{account['id']}/transactions").json()
    assert history["pagination"]["total_records"] == 1


def test_duplicate_reference_with_different_payload_still_rejected(client, account, post):
    post(account["id"], "credit", 100, reference_id="PAY-1")

    res = post(account["id"], "debit", 10, reference_id="PAY-1")

    assert res.status_code == 409
    assert balance_of(client, account["id"]) == 100


def test_same_reference_allowed_on_different_accounts(client, post):
    a = client.post("/api/accounts", json={"name": "A"}).json()
    b = client.post("/api/accounts", json={"name": "B"}).json()

    assert post(a["id"], "credit", 10, reference_id="SHARED").status_code == 201
    assert post(b["id"], "credit", 20, reference_id="SHARED").status_code == 201
    assert balance_of(client, a["id"]) == 10
    assert balance_of(client, b["id"]) == 20


def test_rejected_debit_does_not_consume_reference(client, account, post):
    assert post(account["id"], "debit", 50, reference_id="RETRY-1").status_code == 422
    post(account["id"], "credit", 80)
    assert post(account["id"], "debit", 50, reference_id="RETRY-1").status_code == 201
    assert balance_of(client, account["id"]) == 30


def test_transaction_on_missing_account_is_404(post):
    res = post("nope", "credit", 10)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "refund", "amount": 10, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": 0, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": -5, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": 10.555, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": "abc", "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": True, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": 10, "description": "", "reference_id": "R1"},
        {"type": "credit", "amount": 10, "description": "x", "reference_id": ""},
        {"type": "credit", "amount": 10, "description": "x", "reference_id": "has space"},
        {"type": "credit", "amount": 10, "description": "x"},
        {"amount": 10, "description": "x", "reference_id": "R1"},
        {"type": "credit", "amount": 10, "description": "x", "reference_id": "R1", "balance_after": 5},
    ],
)
def test_invalid_transaction_input(client, account, payload):
    res = client.post(f"/api/accounts/{account['id']}/transactions", json=payload)

    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"
    assert balance_of(client, account["id"]) == 0


def test_decimal_amounts_do_not_drift(client, account, post):
    for _ in range(10):
        post(account["id"], "credit", 0.1)
    post(account["id"], "debit", 0.3)

    assert balance_of(client, account["id"]) == 0.7


def test_amount_accepted_as_string(account, post):
    res = post(account["id"], "credit", "19.99")
    assert res.status_code == 201
    assert res.json()["amount"] == 19.99


def test_type_is_case_insensitive(account, post):
    assert post(account["id"], "CREDIT", 5).json()["type"] == "credit"
