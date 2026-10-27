import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import create_app  # noqa: E402


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "ledger-test.db"


@pytest.fixture
def client(db_path, tmp_path):
    app = create_app(db_path=db_path, frontend_dist=tmp_path / "no-frontend")
    with TestClient(app) as c:
        yield c


@pytest.fixture
def account(client):
    res = client.post("/api/accounts", json={"name": "Asha Raman"})
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def post(client):
    counter = {"n": 0}

    def _post(account_id, type, amount, reference_id=None, description="Test entry"):
        counter["n"] += 1
        return client.post(
            f"/api/accounts/{account_id}/transactions",
            json={
                "type": type,
                "amount": amount,
                "description": description,
                "reference_id": reference_id or f"REF-{counter['n']}",
            },
        )

    return _post
