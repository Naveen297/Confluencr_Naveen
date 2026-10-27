def history(client, account_id, **params):
    res = client.get(f"/api/accounts/{account_id}/transactions", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def seed(account_id, post, n_credits=7, n_debits=5):
    for i in range(n_credits):
        post(account_id, "credit", 100, reference_id=f"C-{i}", description=f"credit {i}")
    for i in range(n_debits):
        post(account_id, "debit", 10, reference_id=f"D-{i}", description=f"debit {i}")


def test_returns_both_types_by_default(client, account, post):
    seed(account["id"], post)

    body = history(client, account["id"], limit=100)

    assert body["pagination"]["total_records"] == 12
    assert {t["type"] for t in body["data"]} == {"credit", "debit"}


def test_filter_by_type(client, account, post):
    seed(account["id"], post)

    credits = history(client, account["id"], type="credit", limit=100)
    debits = history(client, account["id"], type="debit", limit=100)

    assert credits["pagination"]["total_records"] == 7
    assert all(t["type"] == "credit" for t in credits["data"])
    assert debits["pagination"]["total_records"] == 5
    assert all(t["type"] == "debit" for t in debits["data"])


def test_invalid_type_filter(client, account):
    res = client.get(f"/api/accounts/{account['id']}/transactions", params={"type": "refund"})
    assert res.status_code == 422


def test_latest_first(client, account, post):
    seed(account["id"], post)

    data = history(client, account["id"], limit=100)["data"]
    stamps = [t["created_at"] for t in data]

    assert stamps == sorted(stamps, reverse=True)
    assert data[0]["reference_id"] == "D-4"
    assert data[-1]["reference_id"] == "C-0"


def test_pagination_metadata(client, account, post):
    seed(account["id"], post)  # 12 rows

    page1 = history(client, account["id"], page=1, limit=5)
    page3 = history(client, account["id"], page=3, limit=5)

    assert page1["pagination"] == {
        "page": 1,
        "limit": 5,
        "total_records": 12,
        "total_pages": 3,
        "has_next": True,
        "has_previous": False,
    }
    assert len(page1["data"]) == 5
    assert len(page3["data"]) == 2
    assert page3["pagination"]["has_next"] is False
    assert page3["pagination"]["has_previous"] is True


def test_pages_do_not_overlap(client, account, post):
    seed(account["id"], post)

    seen = []
    for page in range(1, 4):
        seen += [t["id"] for t in history(client, account["id"], page=page, limit=5)["data"]]

    assert len(seen) == len(set(seen)) == 12


def test_page_past_the_end_is_empty(client, account, post):
    seed(account["id"], post)

    body = history(client, account["id"], page=99, limit=5)

    assert body["data"] == []
    assert body["pagination"]["total_pages"] == 3


def test_empty_history(client, account):
    body = history(client, account["id"])

    assert body["data"] == []
    assert body["pagination"]["total_records"] == 0
    assert body["pagination"]["total_pages"] == 0


def test_pagination_with_filter(client, account, post):
    seed(account["id"], post)

    body = history(client, account["id"], type="credit", page=2, limit=5)

    assert body["type"] == "credit"
    assert body["pagination"]["total_records"] == 7
    assert body["pagination"]["total_pages"] == 2
    assert len(body["data"]) == 2


def test_invalid_pagination_params(client, account):
    url = f"/api/accounts/{account['id']}/transactions"
    assert client.get(url, params={"page": 0}).status_code == 422
    assert client.get(url, params={"limit": 0}).status_code == 422
    assert client.get(url, params={"limit": 101}).status_code == 422


def test_history_for_missing_account(client):
    res = client.get("/api/accounts/missing/transactions")
    assert res.status_code == 404
