"""Module 7 — Model monitoring core.

Self-contained data-drift + performance-over-time + retraining-trigger logic for the
deployed fraud model. Depends only on numpy/pandas/scipy/scikit-learn — this is the
team's own implementation of what a tool such as Evidently provides, kept dependency-light
and fully auditable (originality requirement).

The served model (XGBoost Base, deployment/model.joblib) scores these 8 features:
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.metrics import precision_score, recall_score, average_precision_score

# The 8 features the deployed model actually consumes (matches deployment/scoring.py).
DEPLOY_FEATURES = [
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "errorBalanceOrig",
    "errorBalanceDest",
    "type_TRANSFER",
]

# ----------------------------------------------------------------------------- #
# Data drift                                                                     #
# ----------------------------------------------------------------------------- #
def population_stability_index(expected, actual, bins: int = 10) -> float:
    """Population Stability Index between a reference (``expected``) and a current
    (``actual``) sample of one feature.

    Bins are the deciles of the reference sample. Rule of thumb: PSI < 0.1 = no
    material shift, 0.1-0.2 = moderate, > 0.2 = significant shift (investigate/retrain).
    Low-cardinality / binary features fall back to a category-frequency comparison.
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    if expected.size == 0 or actual.size == 0:
        return float("nan")

    if np.unique(expected).size <= bins:  # genuinely low-cardinality / binary feature
        cats = np.unique(np.concatenate([expected, actual]))
        e = np.array([(expected == c).mean() for c in cats])
        a = np.array([(actual == c).mean() for c in cats])
    else:
        edges = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
        if edges.size < 2:  # mass collapsed to one value -> no measurable shift
            return 0.0
        edges[0], edges[-1] = -np.inf, np.inf
        e = np.histogram(expected, bins=edges)[0] / expected.size
        a = np.histogram(actual, bins=edges)[0] / actual.size

    eps = 1e-6
    e = np.clip(e, eps, None)
    a = np.clip(a, eps, None)
    return float(np.sum((a - e) * np.log(a / e)))


def drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    features=DEPLOY_FEATURES,
    psi_threshold: float = 0.2,
    ks_stat_threshold: float = 0.1,
) -> pd.DataFrame:
    """Per-feature drift between a reference window and a current window.

    A feature is flagged ``drifted`` when PSI exceeds ``psi_threshold`` OR the
    Kolmogorov-Smirnov **statistic** (an effect size in [0, 1]) exceeds
    ``ks_stat_threshold``.

    We deliberately key the flag on the KS *statistic*, not its p-value: at the
    sample sizes seen in production (hundreds of thousands of transactions) the KS
    p-value is essentially always < 0.01 for any negligible difference, so a
    p-value rule would flag every feature. The statistic and PSI are effect-size
    measures that stay meaningful at scale. The p-value is still reported for
    reference.
    """
    rows = []
    for f in features:
        ref = reference[f].dropna()
        cur = current[f].dropna()
        psi = population_stability_index(ref.values, cur.values)
        ks = ks_2samp(ref.values, cur.values)
        rows.append(
            {
                "feature": f,
                "psi": psi,
                "ks_stat": float(ks.statistic),
                "ks_pvalue": float(ks.pvalue),
                "ref_mean": float(ref.mean()),
                "cur_mean": float(cur.mean()),
                "drifted": bool((psi > psi_threshold) or (ks.statistic > ks_stat_threshold)),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("psi", ascending=False, na_position="last")
        .reset_index(drop=True)
    )


# ----------------------------------------------------------------------------- #
# Performance over time (rolling window)                                         #
# ----------------------------------------------------------------------------- #
def rolling_performance(
    df: pd.DataFrame,
    time_col: str,
    y_col: str,
    score_col: str,
    threshold: float,
    n_windows: int = 12,
) -> pd.DataFrame:
    """Precision / recall / PR-AUC computed on ``n_windows`` equal-width time buckets.

    Simulates production monitoring where labels arrive over time: each bucket is an
    operational window; we track how the operating point (``threshold``) performs as
    the incoming stream evolves.
    """
    d = df[[time_col, y_col, score_col]].dropna().copy()
    d["_bucket"] = pd.cut(d[time_col], bins=n_windows)
    out = []
    for w, g in d.groupby("_bucket", observed=True):
        y = g[y_col].astype(int).to_numpy()
        s = g[score_col].to_numpy()
        pred = (s >= threshold).astype(int)
        has_both = 0 < y.sum() < len(y)
        out.append(
            {
                "window_start": float(w.left),
                "window_end": float(w.right),
                "n": int(len(g)),
                "n_fraud": int(y.sum()),
                "fraud_rate": float(y.mean()) if len(g) else float("nan"),
                "precision": float(precision_score(y, pred, zero_division=0)),
                "recall": float(recall_score(y, pred, zero_division=0)),
                "pr_auc": float(average_precision_score(y, s)) if has_both else float("nan"),
            }
        )
    return pd.DataFrame(out)


# ----------------------------------------------------------------------------- #
# Retraining triggers                                                            #
# ----------------------------------------------------------------------------- #
DEFAULT_TRIGGERS = {
    "psi_significant": 0.20,   # any served feature with PSI above this
    "n_features_drifted": 2,   # at least this many features flagged drifted
    "recall_floor": 0.90,      # rolling recall must not dip below this
    "precision_floor": 0.20,   # rolling precision must not dip below this (imbalance-aware)
    "pr_auc_drop": 0.10,       # rolling PR-AUC must not fall this far below the reference
}


def evaluate_triggers(
    drift_df: pd.DataFrame,
    perf_df: pd.DataFrame,
    ref_pr_auc: float,
    cfg: dict = DEFAULT_TRIGGERS,
) -> dict:
    """Turn drift + rolling-performance evidence into a concrete retrain / hold decision."""
    fired = []

    if len(drift_df):
        n_drift = int(drift_df["drifted"].sum())
        psi_valid = drift_df["psi"].dropna()
        if len(psi_valid):
            max_psi = float(psi_valid.max())
            worst = drift_df.loc[drift_df["psi"].idxmax(), "feature"]
            if max_psi > cfg["psi_significant"]:
                fired.append(
                    f"Data drift: max PSI {max_psi:.3f} > {cfg['psi_significant']} on '{worst}'."
                )
        if n_drift >= cfg["n_features_drifted"]:
            fired.append(
                f"Breadth of drift: {n_drift} served features flagged "
                f"(>= {cfg['n_features_drifted']})."
            )

    if len(perf_df):
        min_recall = float(perf_df["recall"].min())
        min_prec = float(perf_df["precision"].min())
        pr = perf_df["pr_auc"].dropna()
        min_pr = float(pr.min()) if len(pr) else float("nan")
        if min_recall < cfg["recall_floor"]:
            fired.append(
                f"Recall breach: rolling recall fell to {min_recall:.3f} "
                f"< floor {cfg['recall_floor']}."
            )
        if min_prec < cfg["precision_floor"]:
            fired.append(
                f"Precision breach: rolling precision fell to {min_prec:.3f} "
                f"< floor {cfg['precision_floor']}."
            )
        if min_pr == min_pr and (ref_pr_auc - min_pr) > cfg["pr_auc_drop"]:
            fired.append(
                f"PR-AUC decay: rolling PR-AUC fell to {min_pr:.3f}, "
                f"{ref_pr_auc - min_pr:.3f} below reference {ref_pr_auc:.3f}."
            )

    return {"retrain_recommended": bool(fired), "reasons": fired}
