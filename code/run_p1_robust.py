"""Preprint 1: post hoc robustness checks and figures (plan v2, amendment A7).

Usage: python -I run_p1_robust.py <sb0910.csv> <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir> <figure_dir>
"""
import gc, io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, e1, _log  # noqa: E402
from common_v2 import zscore, cox_x  # noqa: E402
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

assist_csv, kt1_zip, contents_zip, out_dir, fig_dir = sys.argv[1:6]
os.makedirs(fig_dir, exist_ok=True)
plt = setup()
res = {"note": "Post hoc checks defined after the confirmatory results were known (amendment A7). HR > 1 = faster mastery."}


def mastery_k(post, k):
    rows = []
    p = post.dropna(subset=["skill"]).sort_values(["user", "skill", "order"])
    users, skills, corr = p["user"].to_numpy(), p["skill"].to_numpy(), p["correct"].to_numpy()
    n, i = len(p), 0
    while i < n:
        j = i + 1
        while j < n and users[j] == users[i] and skills[j] == skills[i]:
            j += 1
        seq = corr[i:j]
        if len(seq) >= 3:
            streak, hit = 0, None
            for t, c in enumerate(seq, start=1):
                streak = streak + 1 if c == 1 else 0
                if streak == k:
                    hit = t
                    break
            rows.append((users[i], skills[i], len(seq), hit if hit else len(seq), 1 if hit else 0))
        i = j
    return pd.DataFrame(rows, columns=["user", "skill", "n_opps", "duration", "event"])


def e1_item_adjusted(post):
    p = post.copy()
    p["logrt"] = p["logrt"] - p.groupby("item")["logrt"].transform("mean")
    return e1(p)


def analyse(df, label, extra=False):
    post, k = prepare(df)
    E1 = e1(post)
    learner = pd.concat([k, E1], axis=1, join="inner").dropna()
    learner["zE1"], learner["zK"] = zscore(learner["E1"]), zscore(learner["K"])
    seq3 = mastery_k(post, 3)
    out = {"E1_k3": cox_x(seq3[seq3["user"].isin(learner.index)], learner, ["zE1", "zK"])}
    _log(f"{label}: k3 done")
    fig_data = None
    if extra:
        for kk in (2, 4):
            s = mastery_k(post, kk)
            out[f"E1_k{kk}"] = cox_x(s[s["user"].isin(learner.index)], learner, ["zE1", "zK"])
            _log(f"{label}: k{kk} done")
        adj = e1_item_adjusted(post).rename("E1adj")
        la = pd.concat([k, adj], axis=1, join="inner").dropna()
        la["zE1"], la["zK"] = zscore(la["E1adj"]), zscore(la["K"])
        out["E1_item_adjusted_k3"] = cox_x(seq3[seq3["user"].isin(la.index)], la, ["zE1", "zK"])
        out["corr_E1_E1adj"] = float(pd.concat([learner["E1"], la["E1adj"]], axis=1, join="inner").corr().iloc[0, 1])
        _log(f"{label}: adjusted done")
        q = pd.qcut(learner["E1"], 4, labels=["Q1 (least slowing)", "Q2", "Q3", "Q4 (most slowing)"])
        s = seq3.merge(q.rename("quartile"), left_on="user", right_index=True)
        fig_data = {}
        for name, g in s.groupby("quartile", observed=True):
            d, e = g["duration"].to_numpy(), g["event"].to_numpy()
            surv, curve = 1.0, []
            for t in range(1, 31):
                at_risk = (d >= t).sum()
                ev = ((d == t) & (e == 1)).sum()
                if at_risk > 0:
                    surv *= 1 - ev / at_risk
                curve.append(1 - surv)
            fig_data[name] = curve
    return out, fig_data


def ednet_sample(seed, exclude=None, target=20000):
    with zipfile.ZipFile(contents_zip) as zc:
        qn = [n for n in zc.namelist() if n.lower().endswith("questions.csv")][0]
        q = pd.read_csv(zc.open(qn))
    q["skill"] = q["tags"].astype(str).str.split(";").str[0]
    key = q.set_index("question_id")[["correct_answer", "skill"]]
    frames = []
    with zipfile.ZipFile(kt1_zip) as z:
        infos = [i for i in z.infolist() if i.filename.endswith(".csv") and i.file_size >= 1200]
        if exclude is None:
            order = np.random.default_rng(seed).permutation(len(infos))
        else:
            excl = set(np.random.default_rng(exclude[0]).permutation(len(infos))[:exclude[1]].tolist())
            order = np.random.default_rng(seed).permutation([k for k in range(len(infos)) if k not in excl])
        for k in order:
            d = pd.read_csv(io.BytesIO(z.read(infos[k])))
            if len(d) < 40:
                continue
            d["user"] = os.path.basename(infos[k].filename)[:-4]
            frames.append(d)
            if len(frames) >= target:
                break
    raw = pd.concat(frames, ignore_index=True).join(key, on="question_id", how="inner")
    df = pd.DataFrame({"user": raw["user"], "order": raw["timestamp"], "skill": raw["skill"], "item": raw["question_id"],
                       "correct": (raw["user_answer"] == raw["correct_answer"]).astype(int),
                       "rt": pd.to_numeric(raw["elapsed_time"], errors="coerce") / 1000.0})
    df["order"] = df["order"].astype("int64") * 1000 + df.groupby("user").cumcount()
    return df


# ASSISTments (Study 1 data), exploratory E1-only model
raw = pd.read_csv(assist_csv, encoding="latin-1", low_memory=False).drop_duplicates(subset="order_id")
raw = raw[raw["original"] == 1]
da = pd.DataFrame({"user": raw["user_id"], "order": raw["order_id"], "item": raw["problem_id"],
                   "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
                   "correct": pd.to_numeric(raw["correct"], errors="coerce"),
                   "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0}).dropna(subset=["correct"])
da["correct"] = (da["correct"] >= 1).astype(int)
res["ASSISTments_study1"], _ = analyse(da, "ASSISTments")
del raw, da; gc.collect()

d1 = ednet_sample(2026)
res["EdNet_study1"], _ = analyse(d1, "EdNet S1")
del d1; gc.collect()

d2 = ednet_sample(2027, exclude=(2026, 20359))
res["EdNet_study2"], curves = analyse(d2, "EdNet S2", extra=True)
del d2; gc.collect()
res["figure_cumulative_mastery"] = curves

# Figure 1: cumulative mastery by E1 quartile (Study 2)
fig, ax = plt.subplots(figsize=(6.3, 3.0))
shades = ["#c6dbef", "#6baed6", "#2171b5", "#08306b"]
for (name, curve), c in zip(curves.items(), shades):
    ax.plot(range(1, 31), curve, color=c, lw=1.8, label=name)
ax.set_xlabel("Responses within a topic")
ax.set_ylabel("Share of topic sequences\nmastered (Kaplan–Meier)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}%"))
ax.set_xlim(1, 30)
ax.legend(title="Post-error slowing", fontsize=8, title_fontsize=8, loc="lower right")
ax.set_title("Learners who slow down more after errors master topics sooner (EdNet, Study 2, 19,883 learners)", loc="left", fontsize=9)
fig.savefig(os.path.join(fig_dir, "fig_p1_mastery_curves.png"))
plt.close(fig)

# Figure 2: hazard ratios per SD of E1 across samples and checks
rows = [("ASSISTments, pupils (Study 1 data, exploratory)", res["ASSISTments_study1"]["E1_k3"]),
        ("EdNet, adults (Study 1 sample, exploratory)", res["EdNet_study1"]["E1_k3"]),
        ("EdNet, adults (Study 2, confirmatory H1)", res["EdNet_study2"]["E1_k3"]),
        ("Study 2: mastery = 2 in a row", res["EdNet_study2"]["E1_k2"]),
        ("Study 2: mastery = 4 in a row", res["EdNet_study2"]["E1_k4"]),
        ("Study 2: E1 adjusted for item time", res["EdNet_study2"]["E1_item_adjusted_k3"])]
fig, ax = plt.subplots(figsize=(6.3, 2.8))
y = np.arange(len(rows))[::-1]
for yi, (lab, r) in zip(y, rows):
    hr, lo, hi = r["zE1"]["HR"], r["zE1"]["95ci"][0], r["zE1"]["95ci"][1]
    col = BLUE if "confirmatory" in lab else DARK if "Study 1" in lab else GREY
    ax.errorbar(hr, yi, xerr=[[hr - lo], [hi - hr]], fmt="s" if "confirmatory" in lab else "o", color=col, capsize=3, ms=5)
    ax.text(1.215, yi, f"{hr:.3f} ({lo:.3f}–{hi:.3f})", va="center", fontsize=8)
ax.axvline(1, color="#999999", lw=1, ls="--")
ax.set_yticks(y, [r[0] for r in rows])
ax.set_xlim(0.95, 1.2)
ax.set_xlabel("Hazard ratio of mastery per SD of post-error slowing (95% CI); > 1 = faster mastery")
fig.savefig(os.path.join(fig_dir, "fig_p1_forest.png"))
plt.close(fig)

with open(os.path.join(out_dir, "p1_robust.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("figure")}, indent=1, ensure_ascii=False))
