"""Shared test fixtures.

Puts the project's script directories on the path and installs a small, deterministic
STAND-IN model so scoring/API tests don't depend on the trained `deployment/model.joblib`
(which needs the 493 MB dataset + a full notebook run to produce). `scoring.py` reads the
model path from the `MODEL_PATH` env var, so we point it at the stub before it is imported.
"""
import os
import sys
import tempfile

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for sub in ("deployment", "monitoring", "slides"):
    p = os.path.join(ROOT, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# Single source of truth for the served feature set (monitoring/ is on sys.path above).
from monitoring_core import DEPLOY_FEATURES  # noqa: E402

# ----- stand-in model, wired in before scoring.py is imported anywhere -----
_STUB_PATH = os.path.join(tempfile.gettempdir(), "fraud_stub_model.joblib")


def _build_stub_bundle(path: str) -> None:
    rng = np.random.default_rng(0)
    n = 1500
    X = pd.DataFrame({f: rng.normal(size=n) for f in DEPLOY_FEATURES})
    # label correlates with the balance-error footprint (mirrors the real model's top signal)
    y = (X["errorBalanceOrig"] + rng.normal(scale=0.3, size=n) > 0).astype(int)
    model = LogisticRegression(max_iter=200).fit(X, y)
    joblib.dump(
        {"model": model, "features": DEPLOY_FEATURES, "threshold": 0.5,
         "block_threshold": 0.8, "model_name": "stub-logreg"},
        path,
    )


_build_stub_bundle(_STUB_PATH)
os.environ["MODEL_PATH"] = _STUB_PATH
# Don't let a real BLOCK_THRESHOLD override leak into tests — use the stub bundle's 0.8.
os.environ.pop("BLOCK_THRESHOLD", None)


@pytest.fixture
def sample_txn():
    return {
        "type": "TRANSFER", "amount": 1000.0, "oldbalanceOrg": 1000.0,
        "newbalanceOrig": 0.0, "oldbalanceDest": 0.0, "newbalanceDest": 0.0,
    }


@pytest.fixture
def ref_cur_frames():
    """A stable reference window and a deliberately drifted current window."""
    rng = np.random.default_rng(7)

    def draw(n, scale, err_rate, fraud_rate, step_lo, step_hi):
        amount = rng.lognormal(np.log(scale), 1.0, n)
        err = np.where(rng.random(n) < err_rate, amount * rng.uniform(0.5, 1.5, n), 0.0)
        y = (rng.random(n) < fraud_rate).astype(int)
        return pd.DataFrame({
            "amount": amount,
            "oldbalanceOrg": amount * rng.uniform(1, 3, n),
            "newbalanceOrig": np.clip(amount * rng.uniform(0, 1, n), 0, None),
            "oldbalanceDest": rng.lognormal(10, 1, n),
            "newbalanceDest": rng.lognormal(10, 1, n),
            "errorBalanceOrig": err,
            "errorBalanceDest": -err * rng.uniform(0, 1, n),
            "type_TRANSFER": (rng.random(n) < 0.5).astype("int8"),
            "isFraud": y,
            "score": np.clip(0.02 + 0.9 * y + rng.normal(0, 0.05, n), 0, 1),
            "step": rng.integers(step_lo, step_hi, n),
        })

    ref = draw(4000, 1e5, 0.30, 0.003, 1, 200)
    cur = draw(4000, 3e5, 0.60, 0.006, 200, 400)  # larger amounts, more errors, more fraud
    return ref, cur
