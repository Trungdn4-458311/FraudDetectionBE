"""Integration test for the monitoring report builder (monitoring/build_monitoring.py)."""
import os

import build_monitoring as bm
from monitoring_core import drift_report, evaluate_triggers, rolling_performance


def test_synthetic_stream_has_required_columns():
    ref, cur, synthetic = bm._synthetic_stream()
    assert synthetic is True
    needed = set(bm.DEPLOY_FEATURES) | {"isFraud", "score", "step"}
    assert needed.issubset(ref.columns)
    assert needed.issubset(cur.columns)


def test_synthetic_stream_pipeline_flags_retrain():
    """The synthetic current window is deliberately drifted -> retrain must fire."""
    ref, cur, _ = bm._synthetic_stream()
    drift = drift_report(ref, cur, bm.DEPLOY_FEATURES)
    perf = rolling_performance(ref, "step", "isFraud", "score", 0.5, n_windows=6)
    out = evaluate_triggers(drift, perf, ref_pr_auc=0.5)
    assert out["retrain_recommended"] is True


def test_main_writes_html_dashboard(tmp_path, monkeypatch):
    # Hermetic: redirect all outputs into tmp and force the synthetic stream so the
    # test never reads/overwrites the repo's real parquet or graded report figures.
    monkeypatch.setattr(bm, "HERE", str(tmp_path))
    monkeypatch.setattr(bm, "FIGDIR", str(tmp_path / "figs"))
    monkeypatch.setattr(bm, "REF_PATH", str(tmp_path / "nope_ref.parquet"))
    monkeypatch.setattr(bm, "CUR_PATH", str(tmp_path / "nope_cur.parquet"))
    bm.main()
    html = os.path.join(bm.HERE, "monitoring_report.html")
    assert os.path.exists(html)
    content = open(html, encoding="utf-8").read()
    assert "Retraining triggers" in content
    assert "Data drift" in content
