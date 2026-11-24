"""Preprint 1, post hoc exploratory (amendment A7e): does the traditional E1 association reflect rapid responding?
Rapid response = raw response time < 10% of the item's median response time in the sample.

Usage: python -I run_p1_rapid.py <sb0910.csv> <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>
"""
import io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, e1, mastery_sequences, _log  # noqa: E402
from common_v2 import zscore, cox_x  # noqa: E402

assist_csv, kt1_zip, contents_zip, out_dir = sys.argv[1:5]


def run(df, label):
    df = df.copy()
    df["rapid"] = (df["rt"] < 0.1 * df.groupby("item")["rt"].transform("median")).astype(float).where(df["rt"].notna())
    post, k = prepare(df)
    E1 = e1(post)
    rapid = post.groupby("user")["rapid"].mean().rename("rapid_share")
    L = pd.concat([k, E1, rapid], axis=1, join="inner").dropna()
    L["zE1"], L["zK"], L["zR"] = zscore(L["E1"]), zscore(L["K"]), zscore(L["rapid_share"])
    seq = mastery_sequences(post)
    s = seq[seq["user"].isin(L.index)]
    q = pd.qcut(L["E1"], 4, labels=["Q1", "Q2", "Q3", "Q4"])
    out = {"n": int(len(L)),
           "rapid_share_mean": float(L["rapid_share"].mean()), "rapid_share_median": float(L["rapid_share"].median()),
           "corr_E1_rapid": float(L[["E1", "rapid_share"]].corr().iloc[0, 1]),
           "rapid_share_by_E1_quartile": {str(a): float(b) for a, b in L.groupby(q, observed=True)["rapid_share"].mean().items()},
           "cox_E1_K": cox_x(s, L, ["zE1", "zK"]),
           "cox_E1_K_rapid": cox_x(s, L, ["zE1", "zK", "zR"])}
    low = L[L["rapid_share"] <= 0.02].copy()
    low["zE1"], low["zK"] = zscore(low["E1"]), zscore(low["K"])
    out["cox_E1_K_learners_rapid_le_2pct"] = cox_x(seq[seq["user"].isin(low.index)], low, ["zE1", "zK"]) | {"n_learners_subset": int(len(low))}
    _log(f"{label} done")
    return out


raw = pd.read_csv(assist_csv, encoding="latin-1", low_memory=False).drop_duplicates(subset="order_id")
raw = raw[raw["original"] == 1]
da = pd.DataFrame({"user": raw["user_id"], "order": raw["order_id"], "item": raw["problem_id"],
                   "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
                   "correct": pd.to_numeric(raw["correct"], errors="coerce"),
                   "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0}).dropna(subset=["correct"])
da["correct"] = (da["correct"] >= 1).astype(int)
res = {"note": "Post hoc exploratory (A7e). HR > 1 = faster mastery.", "ASSISTments": run(da, "ASSISTments")}
del raw, da

with zipfile.ZipFile(contents_zip) as zc:
    q = pd.read_csv(zc.open([n for n in zc.namelist() if n.lower().endswith("questions.csv")][0]))
q["skill"] = q["tags"].astype(str).str.split(";").str[0]
key = q.set_index("question_id")[["correct_answer", "skill"]]
frames = []
with zipfile.ZipFile(kt1_zip) as z:
    infos = [i for i in z.infolist() if i.filename.endswith(".csv") and i.file_size >= 1200]
    excl = set(np.random.default_rng(2026).permutation(len(infos))[:20359].tolist())
    for k in np.random.default_rng(2027).permutation([k for k in range(len(infos)) if k not in excl]):
        d = pd.read_csv(io.BytesIO(z.read(infos[k])))
        if len(d) < 40:
            continue
        d["user"] = os.path.basename(infos[k].filename)[:-4]
        frames.append(d)
        if len(frames) >= 20000:
            break
raw = pd.concat(frames, ignore_index=True).join(key, on="question_id", how="inner")
de = pd.DataFrame({"user": raw["user"], "order": raw["timestamp"], "skill": raw["skill"], "item": raw["question_id"],
                   "correct": (raw["user_answer"] == raw["correct_answer"]).astype(int),
                   "rt": pd.to_numeric(raw["elapsed_time"], errors="coerce") / 1000.0})
de["order"] = de["order"].astype("int64") * 1000 + de.groupby("user").cumcount()
res["EdNet_study2"] = run(de, "EdNet S2")
with open(os.path.join(out_dir, "p1_rapid.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print("ok")
