"""Unit tests for the deployment scoring core (deployment/scoring.py)."""
import scoring


def test_featurize_derives_error_balances_and_type(sample_txn):
    X = scoring.featurize(sample_txn)
    # column set + order must match the model's feature list exactly
    assert list(X.columns) == scoring.FEATURES
    row = X.iloc[0]
    # errorBalanceOrig = newbalanceOrig + amount - oldbalanceOrg
    assert row["errorBalanceOrig"] == 0.0 + 1000.0 - 1000.0
    # errorBalanceDest = oldbalanceDest + amount - newbalanceDest
    assert row["errorBalanceDest"] == 0.0 + 1000.0 - 0.0
    assert row["type_TRANSFER"] == 1


def test_featurize_type_cash_out_is_zero(sample_txn):
    X = scoring.featurize({**sample_txn, "type": "CASH_OUT"})
    assert X.iloc[0]["type_TRANSFER"] == 0


def test_decide_three_tiers():
    # stub bundle: threshold=0.5, block_threshold=0.8
    assert scoring.decide(0.0) == ("APPROVE", "auto-approve")
    assert scoring.decide(0.49) == ("APPROVE", "auto-approve")
    assert scoring.decide(0.5) == ("REVIEW", "manual-review")
    assert scoring.decide(0.79) == ("REVIEW", "manual-review")
    assert scoring.decide(0.8) == ("BLOCK", "auto-block")
    assert scoring.decide(0.999) == ("BLOCK", "auto-block")


def test_decide_monotonic_ordering():
    order = {"APPROVE": 0, "REVIEW": 1, "BLOCK": 2}
    ranks = [order[scoring.decide(p)[0]] for p in [0.1, 0.3, 0.5, 0.7, 0.85, 0.95]]
    assert ranks == sorted(ranks)  # never downgrades as probability rises


def test_score_txn_schema_and_consistency(sample_txn):
    r = scoring.score_txn(sample_txn)
    assert set(r) == {
        "fraud_probability", "flagged_fraud", "decision",
        "risk_tier", "threshold", "block_threshold", "model",
    }
    assert 0.0 <= r["fraud_probability"] <= 1.0
    assert r["decision"] in {"APPROVE", "REVIEW", "BLOCK"}
    # decision + flag must be consistent with the probability and thresholds
    assert r["decision"] == scoring.decide(r["fraud_probability"])[0]
    assert r["flagged_fraud"] == (r["fraud_probability"] >= r["threshold"])
    assert (r["decision"] == "APPROVE") == (not r["flagged_fraud"])
