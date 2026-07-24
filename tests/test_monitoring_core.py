"""Unit tests for the monitoring core (monitoring/monitoring_core.py)."""
import numpy as np
import pandas as pd

import monitoring_core as mc


def test_psi_near_zero_for_identical_distributions():
    rng = np.random.default_rng(0)
    x = rng.normal(size=5000)
    assert mc.population_stability_index(x, x.copy()) < 0.01


def test_psi_large_for_shifted_distribution():
    rng = np.random.default_rng(0)
    a = rng.normal(0, 1, 5000)
    b = rng.normal(3, 1, 5000)  # mean shifted by 3 sigma
    assert mc.population_stability_index(a, b) > 0.5


def test_psi_handles_binary_feature():
    a = np.array([0, 0, 0, 1, 1])
    b = np.array([0, 1, 1, 1, 1])
    val = mc.population_stability_index(a, b)
    assert np.isfinite(val) and val > 0


def test_drift_report_flags_the_drifted_window(ref_cur_frames):
    ref, cur = ref_cur_frames
    rep = mc.drift_report(ref, cur, mc.DEPLOY_FEATURES)
    assert set(["feature", "psi", "ks_stat", "ks_pvalue", "drifted"]).issubset(rep.columns)
    assert len(rep) == len(mc.DEPLOY_FEATURES)
    # amount was scaled up 3x in the current window -> must be flagged
    assert bool(rep.set_index("feature").loc["amount", "drifted"])


def test_drift_report_no_flag_when_identical(ref_cur_frames):
    ref, _ = ref_cur_frames
    rep = mc.drift_report(ref, ref.copy(), mc.DEPLOY_FEATURES)
    assert not rep["drifted"].any()


def test_rolling_performance_perfect_separation():
    # score == label -> at threshold 0.5 every window with fraud has recall=precision=1
    n = 1200
    df = pd.DataFrame({
        "step": np.repeat(np.arange(6), n // 6),
        "isFraud": np.tile([0, 0, 0, 1], n // 4),
    })
    df["score"] = df["isFraud"].astype(float)
    perf = mc.rolling_performance(df, "step", "isFraud", "score", threshold=0.5, n_windows=6)
    assert 0 < len(perf) <= 6 and (perf["n"] > 0).all()
    fraud_windows = perf[perf["n_fraud"] > 0]
    assert (fraud_windows["recall"] == 1.0).all()
    assert (fraud_windows["precision"] == 1.0).all()


def test_effect_size_not_pvalue_drives_drift():
    """Regression: a tiny-but-significant shift at large n must NOT flag drift.
    The KS p-value would reject (over-powered at large n); the effect-size rule must not."""
    rng = np.random.default_rng(3)
    n = 100_000
    ref = pd.DataFrame({"f": rng.normal(0.0, 1.0, n)})
    cur = pd.DataFrame({"f": rng.normal(0.05, 1.0, n)})  # 0.05-sigma shift, huge n
    row = mc.drift_report(ref, cur, ["f"]).iloc[0]
    assert row["ks_pvalue"] < 0.01   # a p-value rule WOULD flag this
    assert row["ks_stat"] < 0.1      # but the effect size is small
    assert row["psi"] < 0.2
    assert not row["drifted"]        # so our effect-size rule correctly does not flag


def test_evaluate_triggers_fires_on_drift_and_decay():
    drift = pd.DataFrame({"feature": ["amount", "x"], "psi": [0.6, 0.3],
                          "drifted": [True, True]})
    perf = pd.DataFrame({"precision": [0.5], "recall": [0.4], "pr_auc": [0.5]})
    out = mc.evaluate_triggers(drift, perf, ref_pr_auc=0.9)
    assert out["retrain_recommended"] is True
    assert len(out["reasons"]) >= 2  # PSI breach + recall breach at least


def test_evaluate_triggers_clears_when_healthy():
    drift = pd.DataFrame({"feature": ["amount"], "psi": [0.05], "drifted": [False]})
    perf = pd.DataFrame({"precision": [0.9], "recall": [0.98], "pr_auc": [0.95]})
    out = mc.evaluate_triggers(drift, perf, ref_pr_auc=0.96)
    assert out["retrain_recommended"] is False
    assert out["reasons"] == []
