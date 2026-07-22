"""Integration tests for the FastAPI scorer (deployment/api.py) via TestClient."""
import pytest
from fastapi.testclient import TestClient

import api

client = TestClient(api.app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["n_features"] == len(api.FEATURES)
    assert "threshold" in body


def test_predict_returns_decision(sample_txn):
    r = client.post("/predict", json=sample_txn)
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] in {"APPROVE", "REVIEW", "BLOCK"}
    assert body["risk_tier"] in {"auto-approve", "manual-review", "auto-block"}
    assert 0.0 <= body["fraud_probability"] <= 1.0


@pytest.mark.parametrize("bad", [
    {"type": "TRANSFER", "amount": -5, "oldbalanceOrg": 0, "newbalanceOrig": 0,
     "oldbalanceDest": 0, "newbalanceDest": 0},                       # negative amount
    {"type": "TRANSFER", "amount": 10},                               # missing fields
])
def test_predict_rejects_invalid_payloads(bad):
    assert client.post("/predict", json=bad).status_code == 422
