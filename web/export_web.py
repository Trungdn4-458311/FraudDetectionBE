"""Export the deployed XGBoost model to a compact JSON the browser can evaluate,
and VERIFY the JS-style tree traversal matches model.predict_proba exactly."""
import json, sys
import numpy as np
import pandas as pd
import xgboost as xgb
import joblib

b = joblib.load("deployment/model.joblib")
model, feats = b["model"], list(b["features"])
threshold, block = float(b["threshold"]), float(b.get("block_threshold", 0.8))
booster = model.get_booster()
trees = [json.loads(t) for t in booster.get_dump(dump_format="json")]


def _fidx(split):
    return feats.index(split) if split in feats else int(str(split)[1:])


def eval_tree(node, x):
    while "leaf" not in node:
        f = _fidx(node["split"])
        go = node["yes"] if x[f] < node["split_condition"] else node["no"]
        node = next(c for c in node["children"] if c["nodeid"] == go)
    return node["leaf"]


def margin_sum(x):
    return sum(eval_tree(t, x) for t in trees)


# --- derive base margin empirically + verify it is constant ---
rng = np.random.default_rng(0)
X = rng.normal(scale=1e5, size=(40, len(feats)))
Xdf = pd.DataFrame(X, columns=feats)
raw = booster.predict(xgb.DMatrix(Xdf), output_margin=True)
sums = np.array([margin_sum(X[i]) for i in range(len(X))])
base = raw - sums
assert np.allclose(base, base[0], atol=1e-4), f"base not constant: {base.min()}..{base.max()}"
base_margin = float(base.mean())

# --- verify probabilities match predict_proba ---
prob_model = model.predict_proba(Xdf)[:, 1]
prob_js = 1.0 / (1.0 + np.exp(-(base_margin + sums)))
max_diff = float(np.max(np.abs(prob_model - prob_js)))
print(f"features       : {feats}")
print(f"n_trees        : {len(trees)}")
print(f"base_margin    : {base_margin:.6f}")
print(f"threshold/block: {threshold} / {block}")
print(f"MAX PROB DIFF (JS-eval vs predict_proba): {max_diff:.2e}")
assert max_diff < 1e-6, "PARITY FAILED"
print("PARITY OK")

out = {"features": feats, "base_margin": base_margin,
       "threshold": threshold, "block_threshold": block, "trees": trees}
with open("docs_model.json", "w") as fh:
    json.dump(out, fh, separators=(",", ":"))
import os
print(f"wrote docs_model.json ({os.path.getsize('docs_model.json')/1024:.0f} KB)")
