"""Preprint 2: post hoc robustness checks and figures (plan v2, amendment A7).

Usage: python -I run_p2_robust.py <sb0910.csv> <EdNet-KT3.zip> <EdNet-Contents.zip> <results_dir> <figure_dir>
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, _log  # noqa: E402
from common_v2 import fe_lpm  # noqa: E402
import kt3_sample  # noqa: E402
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

assist_csv, kt3_zip, contents_zip, out_dir, fig_dir = sys.argv[1:6]
os.makedirs(fig_dir, exist_ok=True)
plt = setup()
res = {"note": "Post hoc checks defined after the confirmatory results were known (amendment A7)."}


def loo_easiness(df, item):
    g = df.groupby(item)["correct"]
    s, n = g.transform("sum"), g.transform("count")
    return ((s - df["correct"]) / (n - 1)).where(n > 1)


def learner_mean_ci(d, cat_col, y, min_n=5):
    m = d.groupby(["user", cat_col])[y].agg(["mean", "size"]).reset_index()
    m = m[m["size"] >= min_n]
    out = m.groupby(cat_col)["mean"].agg(["mean", "std", "size"])
    out["ci"] = 1.96 * out["std"] / np.sqrt(out["size"])
    return out


# ---------------- ASSISTments ----------------
raw = pd.read_csv(assist_csv, encoding="latin-1", low_memory=False)
raw = raw.drop_duplicates(subset="order_id")
raw = raw[raw["original"] == 1]
df = pd.DataFrame({
    "user": raw["user_id"], "order": raw["order_id"], "problem": raw["problem_id"],
    "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
    "correct": pd.to_numeric(raw["correct"], errors="coerce"),
    "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0,
    "help_first": (raw["first_action"] == 1).astype(int),
    "bottom": (raw["bottom_hint"] == 1).astype(int),
    "hints": pd.to_numeric(raw["hint_count"], errors="coerce").fillna(0),
}).dropna(subset=["correct"])
df["correct"] = (df["correct"] >= 1).astype(int)
df["easy"] = loo_easiness(df, "problem")
post, _ = prepare(df)
post = post.sort_values(["user", "skill", "order"])
g = post.groupby(["user", "skill"])
post["next_easy"] = g["easy"].shift(-1)
post["next2_correct"] = g["correct"].shift(-2)
post = post.sort_values(["user", "order"])
nx = post.dropna(subset=["next_same_skill_correct", "skill"]).copy()
X = ["easy", "next_easy", "correct"]
res["A_H4_with_difficulty_controls"] = fe_lpm(nx, "next_same_skill_correct", ["bottom"] + X, ["user", "skill"], "user")
res["A_helpfirst_with_difficulty_controls"] = fe_lpm(nx, "next_same_skill_correct", ["help_first"] + X, ["user", "skill"], "user")
nx2 = post.dropna(subset=["next2_correct", "skill"])
res["A_H4_second_next_problem"] = fe_lpm(nx2, "next2_correct", ["bottom"], ["user", "skill"], "user")
_log("ASSISTments models done")

cats = ["Correct on first attempt", "Error, no hint", "Hints after an attempt,\nanswer not shown",
        "Hint before any attempt,\nanswer not shown", "Answer shown"]
nx["cat"] = np.select(
    [nx["bottom"] == 1, nx["help_first"] == 1, nx["hints"] > 0, nx["correct"] == 0, nx["correct"] == 1],
    [cats[4], cats[3], cats[2], cats[1], cats[0]], default="other")
fa = learner_mean_ci(nx, "cat", "next_same_skill_correct").reindex(cats)
res["A_figure_data"] = {c.replace("\n", " "): {"mean": float(r["mean"]), "ci95": float(r["ci"]), "learners": int(r["size"])}
                        for c, r in fa.iterrows()}
fig, ax = plt.subplots(figsize=(6.3, 2.9))
y = np.arange(len(cats))[::-1]
ax.errorbar(fa["mean"], y, xerr=fa["ci"], fmt="o", color=BLUE, ecolor=BLUE, capsize=3, ms=6)
for yi, (m, n) in zip(y, zip(fa["mean"], fa["size"])):
    ax.text(m + 0.035, yi, f"{100 * m:.0f}%", va="center", fontsize=8, color=DARK)
ax.set_yticks(y, cats)
ax.set_xlim(0.2, 1.0)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}%"))
ax.set_xlabel("Next problem of the same skill answered correctly (learner mean, 95% CI)")
ax.set_title("What happened on a problem, and the next problem of the same skill (ASSISTments, 1,309 pupils)", loc="left", fontsize=9)
fig.savefig(os.path.join(fig_dir, "fig_p2_assistments.png"))
plt.close(fig)

# ---------------- EdNet-KT3 ----------------
raw3, n_drawn = kt3_sample.load_sample(kt3_zip, contents_zip, log=_log)
d3 = pd.DataFrame({"user": raw3["user"], "skill": raw3["tag"], "qid": raw3["item_id"], "correct": raw3["correct"],
                   "rt": np.nan, "viewed": raw3["viewed"], "dwell": raw3["dwell"], "source": raw3["source"],
                   "order": raw3["sub_ts"].astype("int64") * 1000 + raw3.groupby("user").cumcount()})
d3["easy"] = loo_easiness(d3, "qid")
post3, _ = prepare(d3)
post3 = post3.sort_values(["user", "skill", "order"])
post3["next_easy"] = post3.groupby(["user", "skill"])["easy"].shift(-1)
post3 = post3.sort_values(["user", "order"])
err = post3[post3["correct"] == 0].dropna(subset=["next_same_skill_correct"]).copy()
res["B_sample_check"] = {"files_drawn": int(n_drawn), "errors_with_next": int(len(err))}
res["B_H5_with_difficulty_controls"] = fe_lpm(err, "next_same_skill_correct", ["viewed", "easy", "next_easy"], ["user", "skill"], "user")
dw = err[(err["viewed"] == 1) & err["dwell"].between(1, 600)].copy()
lg = np.log(dw["dwell"])
dw["zlogdwell"] = (lg - lg.mean()) / lg.std()
res["B_time_on_explanation_with_difficulty_controls"] = fe_lpm(dw, "next_same_skill_correct", ["zlogdwell", "easy", "next_easy"], ["user", "skill"], "user")
_log("KT3 models done")

dw["decile"] = pd.qcut(dw["dwell"], 10, labels=False, duplicates="drop")
dec = dw.groupby("decile").agg(sec=("dwell", "median"), p=("next_same_skill_correct", "mean"), n=("next_same_skill_correct", "size"))
dec["ci"] = 1.96 * np.sqrt(dec["p"] * (1 - dec["p"]) / dec["n"])
nv = err[err["viewed"] == 0]["next_same_skill_correct"]
res["B_figure_data"] = {"deciles": dec.round(4).reset_index().to_dict(orient="records"),
                        "not_viewed": {"p": float(nv.mean()), "n": int(len(nv))}}
fig, ax = plt.subplots(figsize=(6.3, 2.9))
ax.errorbar(dec["sec"], dec["p"], yerr=dec["ci"], fmt="o-", color=BLUE, capsize=2, ms=4, lw=1.2,
            label="Explanation opened (deciles of time spent)")
ax.axhline(nv.mean(), color=GREY, ls="--", lw=1, label=f"Explanation not opened (n = {len(nv):,})")
ax.set_xscale("log")
ax.set_xticks([2, 5, 10, 20, 50, 100, 200], ["2", "5", "10", "20", "50", "100", "200"])
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}%"))
ax.set_xlabel("Median seconds on the explanation in each decile (log scale)")
ax.set_ylabel("Next answer on the same\ntopic correct")
ax.set_title("After an incorrect answer: time on the explanation and the next answer (EdNet-KT3, 20,000 learners)", loc="left", fontsize=9)
ax.legend(loc="lower left", fontsize=8)
fig.savefig(os.path.join(fig_dir, "fig_p2_ednet.png"))
plt.close(fig)

with open(os.path.join(out_dir, "p2_robust.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if "figure" not in k}, indent=1, ensure_ascii=False))
