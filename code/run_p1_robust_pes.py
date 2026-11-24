"""Preprint 1, post hoc (amendment A7): 'robust' post-error slowing (Dutilh et al., 2012) instead of the
traditional post-error minus post-correct contrast. For each error at t with correct responses at t-1 and t+1,
the learner's slowing is median(log RT[t+1] - log RT[t-1]) (at least 5 such errors).

Usage: python -I run_p1_robust_pes.py <sb0910.csv> <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>
"""
import io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, e1, mastery_sequences, _log  # noqa: E402
from common_v2 import zscore, cox_x, split_half_r  # noqa: E402

assist_csv, kt1_zip, contents_zip, out_dir = sys.argv[1:5]


def robust_pes(post, min_n=5):
    p = post.sort_values(["user", "order"])
    g = p.groupby("user")
    prev_c, next_c = g["correct"].shift(1), g["correct"].shift(-1)
    prev_rt, next_rt = g["logrt"].shift(1), g["logrt"].shift(-1)
    m = (p["correct"] == 0) & (prev_c == 1) & (next_c == 1)
    d = (next_rt - prev_rt)[m].dropna()
    agg = d.groupby(p.loc[d.index, "user"]).agg(["median", "size"])
    return agg.loc[agg["size"] >= min_n, "median"].rename("PESr")


def run(df, label):
    post, k = prepare(df)
    r = robust_pes(post)
    E1 = e1(post)
    learner = pd.concat([k, r], axis=1, join="inner").dropna()
    learner["zE1"], learner["zK"] = zscore(learner["PESr"]), zscore(learner["K"])
    seq = mastery_sequences(post)
    out = {"n_learners_with_robust_pes": int(len(learner)),
           "corr_with_traditional_E1": float(pd.concat([learner["PESr"], E1], axis=1, join="inner").corr().iloc[0, 1]),
           "mean_robust_pes": float(learner["PESr"].mean()),
           "cox_robust_pes": cox_x(seq[seq["user"].isin(learner.index)], learner, ["zE1", "zK"])}
    odd, even = post[post["pidx"] % 2 == 1], post[post["pidx"] % 2 == 0]
    out["split_half_robust_pes"] = split_half_r(robust_pes(odd, 3), robust_pes(even, 3))
    _log(f"{label} done")
    return out


raw = pd.read_csv(assist_csv, encoding="latin-1", low_memory=False).drop_duplicates(subset="order_id")
raw = raw[raw["original"] == 1]
da = pd.DataFrame({"user": raw["user_id"], "order": raw["order_id"],
                   "skill": raw["skill_id"].astype(str).where(raw["skill_id"].notna()),
                   "correct": pd.to_numeric(raw["correct"], errors="coerce"),
                   "rt": pd.to_numeric(raw["ms_first_response"], errors="coerce") / 1000.0}).dropna(subset=["correct"])
da["correct"] = (da["correct"] >= 1).astype(int)
res = {"note": "Post hoc (A7): robust post-error slowing after Dutilh et al. (2012). HR > 1 = faster mastery.",
       "ASSISTments": run(da, "ASSISTments")}
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
de = pd.DataFrame({"user": raw["user"], "order": raw["timestamp"], "skill": raw["skill"],
                   "correct": (raw["user_answer"] == raw["correct_answer"]).astype(int),
                   "rt": pd.to_numeric(raw["elapsed_time"], errors="coerce") / 1000.0})
de["order"] = de["order"].astype("int64") * 1000 + de.groupby("user").cumcount()
res["EdNet_study2"] = run(de, "EdNet S2")
with open(os.path.join(out_dir, "p1_robust_pes.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=1))
