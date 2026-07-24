"""Module 7 — build the monitoring dashboard/report.

Usage (via the reproducible env):
    pixi run monitor

Inputs (produced by the notebook's Module 7 export cell), looked up under monitoring/:
    reference_scored.parquet   reference window: DEPLOY_FEATURES + step + isFraud + score
    current_scored.parquet     later ("incoming") window, same columns
If those are absent (e.g. fresh clone, notebook not yet run), a clearly-labelled
SYNTHETIC demo stream is generated so the dashboard is always reproducible.

Outputs:
    monitoring/monitoring_report.html      self-contained dashboard (drift + perf + triggers)
    report/figures/monitoring_drift.png    figures reused by the LaTeX report
    report/figures/monitoring_performance.png
"""
from __future__ import annotations

import base64
import io
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from monitoring_core import (  # noqa: E402
    DEPLOY_FEATURES,
    drift_report,
    rolling_performance,
    evaluate_triggers,
    DEFAULT_TRIGGERS,
)

REF_PATH = os.path.join(HERE, "reference_scored.parquet")
CUR_PATH = os.path.join(HERE, "current_scored.parquet")
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(ROOT, "deployment", "model.joblib"))
FIGDIR = os.path.join(ROOT, "report", "figures")


# --------------------------------------------------------------------------- #
# Data loading                                                                 #
# --------------------------------------------------------------------------- #
def _score_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    if "score" in df.columns:
        return df
    import joblib

    bundle = joblib.load(MODEL_PATH)
    model, feats = bundle["model"], bundle["features"]
    df = df.copy()
    df["score"] = model.predict_proba(df[feats])[:, 1]
    return df


def _synthetic_stream(seed: int = 42):
    """Schema-correct SIMULATION used only when real exports are absent.

    Reference = a stable population; current = the same population with deliberately
    injected covariate drift (larger amounts, more balance-error mass) and a mild
    performance decay, so every drift/trigger path is exercised and visible.
    """
    rng = np.random.default_rng(seed)

    def draw(n, amount_scale, err_rate, fraud_rate):
        amount = rng.lognormal(mean=np.log(amount_scale), sigma=1.1, size=n)
        old_org = amount * rng.uniform(1.0, 3.0, n)
        new_org = np.clip(old_org - amount, 0, None)
        old_dest = rng.lognormal(mean=11, sigma=1.3, size=n)
        new_dest = old_dest + amount
        err_org = np.where(rng.random(n) < err_rate, amount * rng.uniform(0.5, 1.5, n), 0.0)
        err_dest = np.where(rng.random(n) < err_rate, -amount * rng.uniform(0.2, 1.0, n), 0.0)
        type_transfer = (rng.random(n) < 0.5).astype("int8")
        y = (rng.random(n) < fraud_rate).astype(int)
        # score correlates with balance-error footprint + label (mimics the real model)
        logit = -6 + 3.0 * (err_org > 0) + 2.5 * y + 0.4 * type_transfer + rng.normal(0, 0.5, n)
        score = 1 / (1 + np.exp(-logit))
        return pd.DataFrame(
            {
                "amount": amount,
                "oldbalanceOrg": old_org,
                "newbalanceOrig": new_org,
                "oldbalanceDest": old_dest,
                "newbalanceDest": new_dest,
                "errorBalanceOrig": err_org,
                "errorBalanceDest": err_dest,
                "type_TRANSFER": type_transfer,
                "isFraud": y,
                "score": score,
            }
        )

    ref = draw(20000, amount_scale=1e5, err_rate=0.30, fraud_rate=0.003)
    cur = draw(20000, amount_scale=2.2e5, err_rate=0.55, fraud_rate=0.006)  # drifted
    ref["step"] = rng.integers(1, 200, len(ref))
    cur["step"] = rng.integers(200, 400, len(cur))
    return ref, cur, True


def load_windows():
    if os.path.exists(REF_PATH) and os.path.exists(CUR_PATH):
        ref = _score_if_needed(pd.read_parquet(REF_PATH))
        cur = _score_if_needed(pd.read_parquet(CUR_PATH))
        return ref, cur, False
    return _synthetic_stream()


# --------------------------------------------------------------------------- #
# Charts                                                                        #
# --------------------------------------------------------------------------- #
def _png_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def drift_figure(drift_df, ref, cur):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    colors = ["crimson" if d else "teal" for d in drift_df["drifted"]]
    ax1.barh(drift_df["feature"], drift_df["psi"], color=colors)
    ax1.axvline(DEFAULT_TRIGGERS["psi_significant"], ls="--", color="black", lw=1)
    ax1.set(title="Population Stability Index by feature", xlabel="PSI (>0.2 = significant)")
    ax1.invert_yaxis()
    top = drift_df["feature"].iloc[0]
    lo = float(np.nanpercentile(pd.concat([ref[top], cur[top]]), 1))
    hi = float(np.nanpercentile(pd.concat([ref[top], cur[top]]), 99))
    bins = np.linspace(lo, hi, 40)
    ax2.hist(ref[top].clip(lo, hi), bins=bins, density=True, alpha=0.55, label="reference", color="teal")
    ax2.hist(cur[top].clip(lo, hi), bins=bins, density=True, alpha=0.55, label="current", color="crimson")
    ax2.set(title=f"Distribution shift — {top}", xlabel=top, ylabel="density")
    ax2.legend()
    fig.tight_layout()
    return fig


def performance_figure(perf_df, threshold):
    x = np.arange(len(perf_df))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.plot(x, perf_df["recall"], "-o", label="recall", color="teal")
    ax1.plot(x, perf_df["precision"], "-o", label="precision", color="darkorange")
    ax1.axhline(DEFAULT_TRIGGERS["recall_floor"], ls="--", color="teal", lw=1, alpha=0.6)
    ax1.axhline(DEFAULT_TRIGGERS["precision_floor"], ls="--", color="darkorange", lw=1, alpha=0.6)
    ax1.set(title=f"Rolling precision / recall (threshold={threshold:.2f})",
            xlabel="time window", ylabel="score", ylim=(0, 1.05))
    ax1.legend()
    ax2b = ax2.twinx()
    ax2.bar(x, perf_df["n"], alpha=0.3, color="grey", label="volume")
    ax2b.plot(x, perf_df["pr_auc"], "-o", color="crimson", label="PR-AUC")
    ax2.set(title="Rolling volume & PR-AUC", xlabel="time window", ylabel="transactions")
    ax2b.set_ylabel("PR-AUC")
    ax2b.set_ylim(0, 1.05)
    fig.tight_layout()
    return fig


# --------------------------------------------------------------------------- #
# HTML report                                                                   #
# --------------------------------------------------------------------------- #
def _table(df, fmt):
    cols = "".join(f"<th>{c}</th>" for c in df.columns)
    body = ""
    for _, r in df.iterrows():
        cells = "".join(f"<td>{fmt(c, r[c])}</td>" for c in df.columns)
        body += f"<tr>{cells}</tr>"
    return f"<table><thead><tr>{cols}</tr></thead><tbody>{body}</tbody></table>"


def build_html(drift_df, perf_df, triggers, threshold, ref_pr_auc, synthetic):
    def fmt(col, v):
        if col == "drifted":
            return "🔴 yes" if v else "🟢 no"
        if isinstance(v, float):
            return f"{v:.4f}" if abs(v) < 1000 else f"{v:,.0f}"
        return str(v)

    banner = (
        '<div class="warn">⚠ SIMULATED stream (real reference/current exports not found — '
        "run the notebook Module 7 export to monitor on real data).</div>"
        if synthetic else
        '<div class="ok">Monitoring on real exported reference vs current windows.</div>'
    )
    verdict_cls = "retrain" if triggers["retrain_recommended"] else "hold"
    verdict = "RETRAIN RECOMMENDED" if triggers["retrain_recommended"] else "MODEL HEALTHY — no retrain trigger fired"
    reasons = "".join(f"<li>{r}</li>" for r in triggers["reasons"]) or "<li>All monitored metrics within thresholds.</li>"
    drift_png = _png_b64(drift_figure(drift_df, REF_DF, CUR_DF))
    perf_png = _png_b64(performance_figure(perf_df, threshold))
    # Persist the two figures for the LaTeX report ONLY on real data — never let a
    # synthetic-demo run overwrite the graded report figures.
    if not synthetic:
        os.makedirs(FIGDIR, exist_ok=True)
        drift_figure(drift_df, REF_DF, CUR_DF).savefig(
            os.path.join(FIGDIR, "monitoring_drift.png"), dpi=150, bbox_inches="tight")
        performance_figure(perf_df, threshold).savefig(
            os.path.join(FIGDIR, "monitoring_performance.png"), dpi=150, bbox_inches="tight")

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Fraud model — monitoring report (Module 7)</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:0 auto;max-width:1000px;padding:24px;color:#1a1a1a}}
 h1{{color:#C8102E}} h2{{border-bottom:2px solid #eee;padding-bottom:4px;margin-top:32px}}
 table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0}}
 th,td{{border:1px solid #ddd;padding:6px 8px;text-align:right}} th{{background:#f7f7f7}}
 td:first-child,th:first-child{{text-align:left}}
 .warn{{background:#fff3cd;border:1px solid #ffe08a;padding:10px;border-radius:6px}}
 .ok{{background:#e7f6ec;border:1px solid #a9d9bd;padding:10px;border-radius:6px}}
 .verdict{{padding:14px;border-radius:8px;font-size:18px;font-weight:700;margin:12px 0}}
 .retrain{{background:#fdecea;border:1px solid #f5b5ae;color:#a2231b}}
 .hold{{background:#e7f6ec;border:1px solid #a9d9bd;color:#1e7a45}}
 img{{max-width:100%;border:1px solid #eee;border-radius:6px;margin:8px 0}}
 code{{background:#f2f2f2;padding:1px 5px;border-radius:3px}}
</style></head><body>
<h1>Fraud model — monitoring report</h1>
<p>Module 7 · deployed model <code>XGBoost Base</code> · decision threshold <code>{threshold:.2f}</code>
 · reference PR-AUC <code>{ref_pr_auc:.4f}</code></p>
{banner}
<div class="verdict {verdict_cls}">{verdict}</div>
<ul>{reasons}</ul>

<h2>1. Data drift — incoming vs training distribution</h2>
<p>PSI (deciles of the reference) and the Kolmogorov–Smirnov <b>statistic</b> per served feature.
A feature is flagged when <code>PSI &gt; {DEFAULT_TRIGGERS['psi_significant']}</code> or
<code>KS&nbsp;stat &gt; 0.1</code> — an effect-size rule, since the KS p-value is unreliable at this
sample size (it rejects on any negligible difference).</p>
{_table(drift_df, fmt)}
<img src="data:image/png;base64,{drift_png}">

<h2>2. Performance over time — rolling precision / recall</h2>
<p>The scored stream is bucketed into equal-width time windows on <code>step</code>; precision, recall
and PR-AUC are recomputed per window against the fixed operating threshold.</p>
{_table(perf_df.round(4), fmt)}
<img src="data:image/png;base64,{perf_png}">

<h2>3. Retraining triggers</h2>
<p>Fire a retrain when <b>any</b> of: max PSI &gt; {DEFAULT_TRIGGERS['psi_significant']};
 &ge; {DEFAULT_TRIGGERS['n_features_drifted']} features drifted;
 rolling recall &lt; {DEFAULT_TRIGGERS['recall_floor']};
 rolling precision &lt; {DEFAULT_TRIGGERS['precision_floor']};
 or rolling PR-AUC falls &gt; {DEFAULT_TRIGGERS['pr_auc_drop']} below reference.</p>
</body></html>"""


# module-level handles so the figure helpers can reach the frames
REF_DF = CUR_DF = None


def main():
    global REF_DF, CUR_DF
    import joblib

    ref, cur, synthetic = load_windows()
    REF_DF, CUR_DF = ref, cur
    # The model bundle is the single source of truth for threshold + served features.
    if os.path.exists(MODEL_PATH):
        bundle = joblib.load(MODEL_PATH)
        threshold = float(bundle["threshold"])
        features = list(bundle["features"])
    else:
        threshold, features = 0.21, DEPLOY_FEATURES

    drift_df = drift_report(ref, cur, features)
    stream = pd.concat([ref, cur], ignore_index=True)
    from sklearn.metrics import average_precision_score
    ref_pr_auc = float(average_precision_score(ref["isFraud"], ref["score"]))
    perf_df = rolling_performance(stream, "step", "isFraud", "score", threshold, n_windows=12)
    triggers = evaluate_triggers(drift_df, perf_df, ref_pr_auc)

    html = build_html(drift_df, perf_df, triggers, threshold, ref_pr_auc, synthetic)
    out = os.path.join(HERE, "monitoring_report.html")
    with open(out, "w") as fh:
        fh.write(html)

    print(f"[monitoring] mode={'SYNTHETIC-demo' if synthetic else 'REAL'} "
          f"| drifted features={int(drift_df['drifted'].sum())}/{len(drift_df)} "
          f"| retrain={triggers['retrain_recommended']}")
    for r in triggers["reasons"]:
        print("  -", r)
    print(f"[monitoring] wrote {out}")
    print(f"[monitoring] wrote {FIGDIR}/monitoring_drift.png, monitoring_performance.png")


if __name__ == "__main__":
    main()
