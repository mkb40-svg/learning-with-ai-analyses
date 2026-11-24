"""G1 school pupils: ASSISTments 2009-2010 skill-builder data (corrected, collapsed).

Usage: python -I run_assistments.py <csv_path> <results_dir>

Clarification C4 (made before running): only original (main) problems are used
(original == 1); scaffolding sub-questions are excluded, because an "opportunity"
in the plan is one problem. Duplicate order_id rows are removed.
"""
import json, sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import run_all  # noqa: E402

csv_path, out_dir = sys.argv[1], sys.argv[2]
raw = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
n_raw = len(raw)
raw = raw.drop_duplicates(subset="order_id")
if "original" in raw.columns:
    raw = raw[raw["original"] == 1]
df = pd.DataFrame({
    "user": raw["user_id"],
    "order": raw["order_id"],
    "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
    "correct": pd.to_numeric(raw["correct"], errors="coerce"),
    "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0,
}).dropna(subset=["correct"])
df["correct"] = (df["correct"] >= 1).astype(int)

res, learner = run_all(df, "ASSISTments 2009-2010 (school pupils, mathematics)")
res["n_rows_raw"] = int(n_raw)
res["n_rows_used_main_problems"] = int(len(df))
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "assistments_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
learner.to_csv(os.path.join(out_dir, "assistments_learner_measures.csv"))
print(json.dumps(res, indent=2, ensure_ascii=False))
