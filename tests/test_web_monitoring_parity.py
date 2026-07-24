"""Parity tests: web/monitoring.js must agree with monitoring/monitoring_core.py.

The browser demo re-implements the Module 7 monitoring maths in JavaScript so it can
monitor a live scored stream in the page. That port is only trustworthy if it produces
the same numbers as the Python the report is written from, so these tests feed identical
arrays to both implementations and compare.

Mirrors the parity check web/export_web.py already runs for the model itself. Skipped
when node is unavailable (the JS is not otherwise needed to build any deliverable).
"""
import json
import os
import shutil
import subprocess

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score

import monitoring_core as mc

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONITORING_JS = os.path.join(ROOT, "web", "monitoring.js")

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None or not os.path.exists(MONITORING_JS),
    reason="node (or web/monitoring.js) not available",
)

# Node harness: reads a JSON job from argv[1], writes JSON results to stdout.
_HARNESS = r"""
const M = require(process.argv[2]);
const job = JSON.parse(require("fs").readFileSync(process.argv[3], "utf8"));
const out = {};
if (job.psi) out.psi = job.psi.map(c => M.populationStabilityIndex(c[0], c[1]));
if (job.ks) out.ks = job.ks.map(c => M.ksStat(c[0], c[1]));
if (job.ap) out.ap = job.ap.map(c => M.averagePrecision(c[0], c[1]));
if (job.drift) {
  out.drift = M.driftReport(job.drift.ref, job.drift.cur, job.drift.features);
}
if (job.perf) {
  out.perf = M.rollingPerformance(job.perf.rows, "step", "isFraud", "score",
                                  job.perf.threshold, job.perf.n_windows);
}
if (job.triggers) {
  out.triggers = M.evaluateTriggers(job.triggers.drift, job.triggers.perf,
                                    job.triggers.ref_pr_auc);
}
process.stdout.write(JSON.stringify(out));
"""


def run_js(tmp_path, job):
    harness = tmp_path / "harness.js"
    harness.write_text(_HARNESS)
    job_file = tmp_path / "job.json"
    job_file.write_text(json.dumps(job))
    proc = subprocess.run(
        ["node", str(harness), MONITORING_JS, str(job_file)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    return json.loads(proc.stdout)


# --------------------------------------------------------------------------- #
# Data drift                                                                   #
# --------------------------------------------------------------------------- #
def test_psi_matches_python(tmp_path):
    rng = np.random.default_rng(0)
    cases = [
        (rng.normal(0, 1, 3000), rng.normal(0, 1, 3000)),      # no shift
        (rng.normal(0, 1, 3000), rng.normal(1.5, 1, 3000)),    # mean shift
        (rng.lognormal(11, 1.2, 3000), rng.lognormal(12, 1.4, 3000)),  # heavy tail
        (rng.integers(0, 2, 2000).astype(float),               # binary -> category path
         rng.integers(0, 2, 2000).astype(float)),
        (np.zeros(500), np.zeros(500)),                        # degenerate
    ]
    got = run_js(tmp_path, {"psi": [[a.tolist(), b.tolist()] for a, b in cases]})["psi"]
    for (a, b), js in zip(cases, got):
        py = mc.population_stability_index(a, b)
        assert js == pytest.approx(py, abs=1e-9), f"PSI mismatch: py={py} js={js}"


def test_ks_statistic_matches_python(tmp_path):
    from scipy.stats import ks_2samp

    rng = np.random.default_rng(1)
    cases = [
        (rng.normal(0, 1, 1500), rng.normal(0, 1, 1500)),
        (rng.normal(0, 1, 1500), rng.normal(0.8, 1.3, 900)),
        (rng.lognormal(10, 1, 800), rng.lognormal(11, 1, 1200)),
    ]
    got = run_js(tmp_path, {"ks": [[a.tolist(), b.tolist()] for a, b in cases]})["ks"]
    for (a, b), js in zip(cases, got):
        py = float(ks_2samp(a, b).statistic)
        assert js == pytest.approx(py, abs=1e-12), f"KS mismatch: py={py} js={js}"


def test_drift_report_matches_python(tmp_path, ref_cur_frames):
    ref, cur = ref_cur_frames
    feats = mc.DEPLOY_FEATURES
    job = {"drift": {
        "ref": ref[feats].to_dict("records"),
        "cur": cur[feats].to_dict("records"),
        "features": feats,
    }}
    js_rows = run_js(tmp_path, job)["drift"]
    py = mc.drift_report(ref, cur, feats)

    assert [r["feature"] for r in js_rows] == list(py["feature"]), "row order differs"
    for js_row, (_, py_row) in zip(js_rows, py.iterrows()):
        f = js_row["feature"]
        assert js_row["psi"] == pytest.approx(py_row["psi"], abs=1e-9), f"psi {f}"
        assert js_row["ks_stat"] == pytest.approx(py_row["ks_stat"], abs=1e-12), f"ks {f}"
        assert js_row["drifted"] is bool(py_row["drifted"]), f"drifted flag {f}"


# --------------------------------------------------------------------------- #
# Performance over time                                                        #
# --------------------------------------------------------------------------- #
def test_average_precision_matches_sklearn(tmp_path):
    rng = np.random.default_rng(2)
    cases = []
    for n, rate in [(400, 0.05), (1000, 0.2), (250, 0.5)]:
        y = (rng.random(n) < rate).astype(int)
        if y.sum() in (0, n):
            y[0], y[1] = 0, 1
        s = np.clip(0.1 + 0.6 * y + rng.normal(0, 0.25, n), 0, 1)
        cases.append((y, s))
    # a case with tied scores, which is where a naive AP port diverges
    y = np.array([0, 1, 1, 0, 1, 0, 0, 1])
    s = np.array([0.2, 0.9, 0.9, 0.2, 0.5, 0.5, 0.1, 0.9])
    cases.append((y, s))

    got = run_js(tmp_path, {"ap": [[y.tolist(), s.tolist()] for y, s in cases]})["ap"]
    for (y, s), js in zip(cases, got):
        py = float(average_precision_score(y, s))
        assert js == pytest.approx(py, abs=1e-12), f"AP mismatch: py={py} js={js}"


def test_rolling_performance_matches_python(tmp_path, ref_cur_frames):
    ref, cur = ref_cur_frames
    stream = pd.concat([ref, cur], ignore_index=True)
    cols = ["step", "isFraud", "score"]
    rows = stream[cols].astype(float).to_dict("records")
    threshold, n_windows = 0.5, 12

    js_rows = run_js(tmp_path, {"perf": {
        "rows": rows, "threshold": threshold, "n_windows": n_windows}})["perf"]
    py = mc.rolling_performance(stream, "step", "isFraud", "score", threshold, n_windows)

    assert len(js_rows) == len(py), f"window count differs: js={len(js_rows)} py={len(py)}"
    for i, (js_row, (_, py_row)) in enumerate(zip(js_rows, py.iterrows())):
        assert js_row["n"] == int(py_row["n"]), f"window {i} size"
        assert js_row["n_fraud"] == int(py_row["n_fraud"]), f"window {i} fraud count"
        assert js_row["precision"] == pytest.approx(py_row["precision"], abs=1e-12)
        assert js_row["recall"] == pytest.approx(py_row["recall"], abs=1e-12)
        if pd.isna(py_row["pr_auc"]):
            assert js_row["pr_auc"] is None or np.isnan(js_row["pr_auc"])
        else:
            assert js_row["pr_auc"] == pytest.approx(py_row["pr_auc"], abs=1e-12)


# --------------------------------------------------------------------------- #
# Retraining triggers                                                          #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "drift, perf, ref_pr_auc",
    [
        # healthy: nothing fires
        ([{"feature": "amount", "psi": 0.05, "drifted": False}],
         [{"precision": 0.91, "recall": 0.98, "pr_auc": 0.95}], 0.96),
        # drift breadth + PSI + recall + precision + PR-AUC all fire
        ([{"feature": "amount", "psi": 0.63, "drifted": True},
          {"feature": "errorBalanceDest", "psi": 0.31, "drifted": True}],
         [{"precision": 0.15, "recall": 0.42, "pr_auc": 0.51}], 0.94),
        # only the recall floor breaches
        ([{"feature": "amount", "psi": 0.02, "drifted": False}],
         [{"precision": 0.80, "recall": 0.71, "pr_auc": 0.93}], 0.95),
    ],
)
def test_evaluate_triggers_matches_python(tmp_path, drift, perf, ref_pr_auc):
    js = run_js(tmp_path, {"triggers": {
        "drift": drift, "perf": perf, "ref_pr_auc": ref_pr_auc}})["triggers"]
    py = mc.evaluate_triggers(pd.DataFrame(drift), pd.DataFrame(perf), ref_pr_auc)

    assert js["retrain_recommended"] == py["retrain_recommended"]
    assert js["reasons"] == py["reasons"], (
        f"trigger text differs:\n  js={js['reasons']}\n  py={py['reasons']}"
    )
