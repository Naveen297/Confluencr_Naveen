from datetime import datetime


def test_create_account_returns_required_fields(client):
    res = client.post("/api/accounts", json={"name": "Asha Raman"})

    assert res.status_code == 201
    body = res.json()
    assert set(body) == {"id", "name", "balance", "created_at"}
    assert body["name"] == "Asha Raman"
    assert body["balance"] == 0
    datetime.fromisoformat(body["created_at"].replace("Z", "+00:00"))


def test_account_ids_are_unique(client):
    ids = {client.post("/api/accounts", json={"name": f"User {i}"}).json()["id"] for i in range(25)}
    assert len(ids) == 25


def test_name_is_required(client):
    res = client.post("/api/accounts", json={})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"


def test_blank_name_is_rejected(client):
    res = client.post("/api/accounts", json={"name": "   "})
    assert res.status_code == 422


def test_name_is_trimmed(client):
    res = client.post("/api/accounts", json={"name": "  Dev Kumar  "})
    assert res.json()["name"] == "Dev Kumar"


def test_client_cannot_set_initial_balance(client):
    res = client.post("/api/accounts", json={"name": "Greedy", "balance": 1000})

    assert res.status_code == 422
    assert "balance" in res.json()["error"]["message"]
    assert client.get("/api/accounts").json()["total_records"] == 0


def test_client_cannot_set_id_or_created_at(client):
    res = client.post(
        "/api/accounts",
        json={"name": "Sneaky", "id": "my-id", "created_at": "2000-01-01T00:00:00Z"},
    )
    assert res.status_code == 422


def test_get_balance(client, account, post):
    post(account["id"], "credit", 120.5)

    res = client.get(f"/api/accounts/{account['id']}/balance")

    assert res.status_code == 200
    body = res.json()
    assert body["account_id"] == account["id"]
    assert body["balance"] == 120.5


def test_balance_for_missing_account_is_404(client):
    res = client.get("/api/accounts/does-not-exist/balance")

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def test_account_detail_includes_summary(client, account, post):
    post(account["id"], "credit", 100)
    post(account["id"], "debit", 40)

    body = client.get(f"/api/accounts/{account['id']}").json()

    assert body["balance"] == 60
    assert body["summary"]["total_credits"] == 100
    assert body["summary"]["total_debits"] == 40
    assert body["summary"]["transaction_count"] == 2
    assert body["summary"]["credit_count"] == 1
    assert body["summary"]["debit_count"] == 1


def test_list_accounts_newest_first_and_search(client):
    for name in ["Asha", "Bilal", "Chen"]:
        client.post("/api/accounts", json={"name": name})

    names = [a["name"] for a in client.get("/api/accounts").json()["data"]]
    assert names == ["Chen", "Bilal", "Asha"]

    found = client.get("/api/accounts", params={"search": "bil"}).json()
    assert [a["name"] for a in found["data"]] == ["Bilal"]
