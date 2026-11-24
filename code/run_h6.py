"""H6 (plan v2, amendments A1 and A4): quiz attempt review and final course mark, Universiti Malaya SED.

Usage: python -I run_h6.py <sed_dir> <results_dir>
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import _log  # noqa: E402
from common_v2 import fe_lpm  # noqa: E402

sed, out_dir = sys.argv[1], sys.argv[2]
log = pd.read_csv(os.path.join(sed, "Student_log.csv"),
                  usecols=["userid", "component", "action", "target", "courseid", "timecreated"], dtype=str)
log = log.dropna(subset=["userid", "courseid"])
log["key"] = log["userid"] + "_" + log["courseid"]
n_actions = log.groupby("key").size().rename("n_actions")
q = log[(log["component"] == "mod_quiz") & (log["target"] == "attempt") & log["action"].isin(["submitted", "reviewed"])].copy()
q["t"] = pd.to_datetime(q["timecreated"])
sub = q[q["action"] == "submitted"][["key", "t"]].rename(columns={"t": "ts"}).sort_values("ts")
rev = q[q["action"] == "reviewed"][["key", "t"]].rename(columns={"t": "tr"}).sort_values("tr")
_log(f"log rows {len(log)}, submissions {len(sub)}, reviews {len(rev)}")

r1 = rev.copy(); r1["ts"] = r1["tr"]
m = pd.merge_asof(sub, r1, on="ts", by="key", direction="forward")
sub["review_24h"] = ((m["tr"] - m["ts"]).dt.total_seconds() <= 86400).to_numpy().astype(int)  # A1
s2 = sub[["key", "ts"]].copy(); s2["ts61"] = s2["ts"] + pd.Timedelta(seconds=61)
r2 = rev.copy(); r2["ts61"] = r2["tr"]
m2 = pd.merge_asof(s2.sort_values("ts61"), r2.sort_values("ts61"), on="ts61", by="key", direction="forward")
m2 = m2.set_index(s2.sort_values("ts61").index).reindex(sub.index)
sub["returning_review"] = ((m2["tr"] - m2["ts"]).dt.total_seconds() <= 7 * 86400).astype(int)  # A4 exploratory

pair = sub.groupby("key").agg(n_submissions=("ts", "size"), review_share=("review_24h", "mean"),
                              returning_share=("returning_review", "mean")).join(n_actions)
g = pd.read_csv(os.path.join(sed, "Student_grade_detailed.csv"), dtype=str)
g["mark"] = pd.to_numeric(g["formatted agreed mark"], errors="coerce")
g["key"] = g["userid"] + "_" + g["courseid"]
d = pair.join(g.set_index("key")[["userid", "courseid", "mark"]], how="inner").dropna(subset=["mark"])
d["log_actions"] = np.log(d["n_actions"])
_log(f"analysable student-course pairs {len(d)}")

res = {"dataset": "SED, Universiti Malaya Moodle logs, Sem II 2018/19",
       "n_pairs": int(len(d)), "n_students": int(d["userid"].nunique()), "n_courses": int(d["courseid"].nunique()),
       "descriptives": d[["mark", "review_share", "returning_share", "n_submissions", "n_actions"]].describe().round(3).to_dict()}
res["H6_fe"] = fe_lpm(d, "mark", ["review_share", "log_actions"], ["courseid"], "userid")
res["H6_review_share_sd"] = float(d["review_share"].std())
res["EXPLORATORY_A4_returning_review"] = fe_lpm(d, "mark", ["returning_share", "log_actions"], ["courseid"], "userid")
res["EXPLORATORY_A4_returning_share_sd"] = float(d["returning_share"].std())
_log("H6 done")
with open(os.path.join(out_dir, "h6_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
