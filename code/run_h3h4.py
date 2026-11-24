"""H3, H4 (plan v2, amendment A2: C11-C12): help timing in ASSISTments 2009-10.

Usage: python -I run_h3h4.py <sb0910.csv> <results_dir>
"""
import json, os, sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, mastery_sequences, _log  # noqa: E402
from common_v2 import zscore, cox_x, fe_lpm  # noqa: E402

csv_path, out_dir = sys.argv[1], sys.argv[2]
raw = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
raw = raw.drop_duplicates(subset="order_id")
raw = raw[raw["original"] == 1]  # C4 (Study 1)
df = pd.DataFrame({
    "user": raw["user_id"], "order": raw["order_id"],
    "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
    "correct": pd.to_numeric(raw["correct"], errors="coerce"),
    "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0,
    "help_first": (raw["first_action"] == 1).astype(int),
    "bottom": (raw["bottom_hint"] == 1).astype(int),  # C12: missing = no bottom-out hint
}).dropna(subset=["correct"])
df["correct"] = (df["correct"] >= 1).astype(int)

post, k = prepare(df); _log(f"post rows {len(post)}, learners {post['user'].nunique()}")
res = {"dataset": "ASSISTments 2009-2010 skill builder, main problems", "n_rows_post": int(len(post)),
       "n_learners_eligible": int(post["user"].nunique()),
       "share_help_first_rows": float(post["help_first"].mean()), "share_bottom_rows": float(post["bottom"].mean())}

# H3
share = post.groupby("user")["help_first"].mean().rename("help_first_share")
learner = pd.concat([k, share], axis=1, join="inner").dropna()
learner["zHelp"], learner["zK"] = zscore(learner["help_first_share"]), zscore(learner["K"])
seq = mastery_sequences(post)
res["H3_descriptives"] = learner[["K", "help_first_share"]].describe().round(4).to_dict()
res["H3_cox"] = cox_x(seq[seq["user"].isin(learner.index)], learner, ["zHelp", "zK"]); _log("H3 done")

# H4 and exploratory checks: next problem of the same skill
nx = post.dropna(subset=["next_same_skill_correct", "skill"]).copy()
res["H4_lpm"] = fe_lpm(nx, "next_same_skill_correct", ["bottom"], ["user", "skill"], "user"); _log("H4 done")
res["EXPLORATORY_H4_incorrect_only"] = fe_lpm(nx[nx["correct"] == 0], "next_same_skill_correct", ["bottom"], ["user", "skill"], "user")
res["EXPLORATORY_H3_within_learner_next_correct_after_help_first"] = fe_lpm(
    nx, "next_same_skill_correct", ["help_first"], ["user", "skill"], "user")
_log("exploratory done")

with open(os.path.join(out_dir, "h3h4_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
