"""Preprint 3: post hoc robustness checks and figures (plan v2, amendment A7).

Usage: python -I run_p3_robust.py <CY08MSP_STU_QQQ.SAV> <sed_dir> <results_dir> <figure_dir>
"""
import gc, json, os, sys
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import _log  # noqa: E402
from common_v2 import fe_lpm  # noqa: E402
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

sav, sed, out_dir, fig_dir = sys.argv[1:5]
os.makedirs(fig_dir, exist_ok=True)
plt = setup()
res = {"note": "Post hoc checks defined after the confirmatory results were known (amendment A7)."}

# ---------------- PISA 2022 Malaysia ----------------
PV = [f"PV{i}MATH" for i in range(1, 11)]
RW = [f"W_FSTURWT{i}" for i in range(1, 81)]
df, _ = pyreadstat.read_sav(sav, usecols=["CNT", "ST307Q06JA", "ST307Q10JA", "PERSEVAGR", "ESCS", "ST004D01T", "W_FSTUWT"] + PV + RW,
                            apply_value_formats=False)
d = df[df["CNT"] == "MYS"].copy()
del df; gc.collect()
d["giveup"] = d["ST307Q06JA"].where(d["ST307Q06JA"].between(1, 5))
d["male"] = (d["ST004D01T"] == 2).astype(float).where(d["ST004D01T"].isin([1, 2]))
d["ESCS"] = d["ESCS"].where(d["ESCS"].abs() < 90)
d["PERSEV"] = d["PERSEVAGR"].where(d["PERSEVAGR"].abs() < 90)
d["giveup_easily"] = d["ST307Q10JA"].where(d["ST307Q10JA"].between(1, 5))


def pisa_wls(data, cols, names, intercept=True):
    X = data[cols].to_numpy(float)
    if intercept:
        X = np.column_stack([np.ones(len(data)), X])
        names = ["const"] + names

    def fit(y, w):
        Xw = X * w[:, None]
        return np.linalg.solve(X.T @ Xw, Xw.T @ y)
    est, sv = [], []
    for pv in PV:
        y = data[pv].to_numpy(float)
        b = fit(y, data["W_FSTUWT"].to_numpy(float))
        reps = np.array([fit(y, data[r].to_numpy(float)) for r in RW])
        est.append(b); sv.append(((reps - b) ** 2).sum(axis=0) / 20.0)
    est, sv = np.array(est), np.array(sv)
    M = len(PV); b = est.mean(0); U = sv.mean(0); Bv = est.var(0, ddof=1)
    se = np.sqrt(U + (1 + 1 / M) * Bv)
    r = (1 + 1 / M) * Bv / U; dfr = (M - 1) * (1 + 1 / r) ** 2
    p = 2 * stats.t.sf(np.abs(b / se), dfr)
    return {n: {"b": float(b[i]), "se": float(se[i]), "95ci": [float(b[i] - 1.96 * se[i]), float(b[i] + 1.96 * se[i])],
                "p_two_sided": float(p[i])} for i, n in enumerate(names)}


res["PISA_PERSEVAGR_available_for_MYS"] = int(d["PERSEV"].notna().sum())  # 0: index missing for Malaysia in the database
a = d.dropna(subset=["giveup_easily", "ESCS", "male", "W_FSTUWT"])
res["PISA_item_give_up_easily"] = {"n": int(len(a)), "model": pisa_wls(a, ["giveup_easily", "ESCS", "male"], ["give_up_easily", "ESCS", "male"])}
c = d.dropna(subset=["giveup", "ESCS", "male", "W_FSTUWT"]).copy()
for v in (1, 3, 4, 5):
    c[f"g{v}"] = (c["giveup"] == v).astype(float)
res["PISA_item_as_categories_ref_disagree"] = {"n": int(len(c)), "model": pisa_wls(c, ["g1", "g3", "g4", "g5", "ESCS", "male"],
                                                                                   ["strongly_disagree", "neither", "agree", "strongly_agree", "ESCS", "male"])}
for v in (1, 2, 3, 4, 5):
    c[f"d{v}"] = (c["giveup"] == v).astype(float)
means = pisa_wls(c, [f"d{v}" for v in (1, 2, 3, 4, 5)], ["1", "2", "3", "4", "5"], intercept=False)
labels = ["Strongly\ndisagree", "Disagree", "Neither", "Agree", "Strongly\nagree"]
share = c.groupby("giveup")["W_FSTUWT"].sum() / c["W_FSTUWT"].sum()
res["PISA_figure_means"] = {lab.replace("\n", " "): {"mean": means[str(v)]["b"], "ci95": 1.96 * means[str(v)]["se"],
                                                       "weighted_share": float(share.loc[v]), "n": int((c["giveup"] == v).sum())}
                            for v, lab in zip((1, 2, 3, 4, 5), labels)}
_log("PISA done")
del d, a, c; gc.collect()

# ---------------- SED, Universiti Malaya ----------------
log = pd.read_csv(os.path.join(sed, "Student_log.csv"), usecols=["userid", "component", "action", "target", "courseid", "timecreated"], dtype=str)
log = log.dropna(subset=["userid", "courseid"])
log["key"] = log["userid"] + "_" + log["courseid"]
n_actions = log.groupby("key").size().rename("n_actions")
q = log[(log["component"] == "mod_quiz") & (log["target"] == "attempt") & log["action"].isin(["submitted", "reviewed"])].copy()
del log; gc.collect()
q["t"] = pd.to_datetime(q["timecreated"])
sub = q[q["action"] == "submitted"][["key", "t"]].rename(columns={"t": "ts"}).sort_values("ts")
rev = q[q["action"] == "reviewed"][["key", "t"]].rename(columns={"t": "tr"}).sort_values("tr")
r1 = rev.copy(); r1["ts"] = r1["tr"]
m = pd.merge_asof(sub, r1, on="ts", by="key", direction="forward")
sub["review_24h"] = ((m["tr"] - m["ts"]).dt.total_seconds() <= 86400).to_numpy().astype(int)
s2 = sub[["key", "ts"]].copy(); s2["ts61"] = s2["ts"] + pd.Timedelta(seconds=61)
r2 = rev.copy(); r2["ts61"] = r2["tr"]
m2 = pd.merge_asof(s2.sort_values("ts61"), r2.sort_values("ts61"), on="ts61", by="key", direction="forward")
m2 = m2.set_index(s2.sort_values("ts61").index).reindex(sub.index)
sub["returning"] = ((m2["tr"] - m2["ts"]).dt.total_seconds() <= 7 * 86400).astype(int)
pair = sub.groupby("key").agg(n_sub=("ts", "size"), review_share=("review_24h", "mean"), returning_share=("returning", "mean")).join(n_actions)
g = pd.read_csv(os.path.join(sed, "Student_grade_detailed.csv"), dtype=str)
g["mark"] = pd.to_numeric(g["formatted agreed mark"], errors="coerce")
g["key"] = g["userid"] + "_" + g["courseid"]
dd = pair.join(g.set_index("key")[["userid", "courseid", "mark"]], how="inner").dropna(subset=["mark"])
dd["log_actions"], dd["log_sub"] = np.log(dd["n_actions"]), np.log(dd["n_sub"])
res["SED_H6_plus_submissions_control"] = fe_lpm(dd, "mark", ["review_share", "log_actions", "log_sub"], ["courseid"], "userid")
res["SED_returning_plus_submissions_control"] = fe_lpm(dd, "mark", ["returning_share", "log_actions", "log_sub"], ["courseid"], "userid")
var_courses = dd.groupby("courseid")["review_share"].std()
vv = dd[dd["courseid"].isin(var_courses[var_courses > 0].index)]
res["SED_H6_courses_with_variation"] = fe_lpm(vv, "mark", ["review_share", "log_actions"], ["courseid"], "userid") | {"n_courses": int(vv["courseid"].nunique())}
dd["mark_c"] = dd["mark"] - dd.groupby("courseid")["mark"].transform("mean")
dd["ret_grp"] = pd.cut(dd["returning_share"], [-0.01, 0.0, 0.5, 1.0], labels=["None", "Up to half", "More than half"])
fg = dd.groupby("ret_grp", observed=True)["mark_c"].agg(["mean", "std", "size"])
fg["ci"] = 1.96 * fg["std"] / np.sqrt(fg["size"])
res["SED_figure_returning_groups"] = fg.round(3).reset_index().astype({"ret_grp": str}).to_dict(orient="records")
_log("SED done")

# Figure: two panels
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.6, 2.9), gridspec_kw={"width_ratios": [1.25, 1]})
fm = res["PISA_figure_means"]
x = np.arange(5)
ax1.errorbar(x, [v["mean"] for v in fm.values()], yerr=[v["ci95"] for v in fm.values()], fmt="o", color=BLUE, capsize=3, ms=5)
for xi, v in zip(x, fm.values()):
    ax1.text(xi, v["mean"] + v["ci95"] + 4, f"{100 * v['weighted_share']:.0f}%", ha="center", fontsize=7, color=GREY)
ax1.set_xticks(x, labels, fontsize=7.5)
ax1.set_ylabel("Mathematics score (mean, 95% CI)")
ax1.set_title("A. PISA 2022 Malaysia:\n\"I give up after making mistakes\"", loc="left", fontsize=8.5)
ax2.errorbar(np.arange(len(fg)), fg["mean"], yerr=fg["ci"], fmt="o", color=BLUE, capsize=3, ms=5)
ax2.axhline(0, color="#999999", lw=1, ls="--")
ax2.set_xticks(np.arange(len(fg)), [f"{lab}\n(n = {n:,})" for lab, n in zip(fg.index.astype(str), fg["size"])], fontsize=7.5)
ax2.set_ylabel("Course mark vs course mean")
ax2.set_title("B. Universiti Malaya: share of quiz attempts\nreturned to after more than 60 s", loc="left", fontsize=8.5)
fig.tight_layout()
fig.savefig(os.path.join(fig_dir, "fig_p3_malaysia.png"))
plt.close(fig)

with open(os.path.join(out_dir, "p3_robust.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
