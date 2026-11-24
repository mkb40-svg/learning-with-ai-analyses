"""H1, H2 (plan v2, amendment A2: C8-C10): replication of E1 on a fresh EdNet-KT1 sample.

Usage: python -I run_h1h2.py <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>
"""
import io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, e1, mastery_sequences, _log  # noqa: E402
from common_v2 import zscore, cox_x, split_half_r  # noqa: E402

kt1_zip, contents_zip, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
TARGET, MIN_ROWS = 20000, 40
STUDY1_SEED, STUDY1_DRAWN, SEED = 2026, 20359, 2027

with zipfile.ZipFile(contents_zip) as zc:
    qname = [n for n in zc.namelist() if n.lower().endswith("questions.csv")][0]
    q = pd.read_csv(zc.open(qname))
q["skill"] = q["tags"].astype(str).str.split(";").str[0]
key = q.set_index("question_id")[["correct_answer", "skill"]]

frames, n_drawn = [], 0
with zipfile.ZipFile(kt1_zip) as z:
    infos = [i for i in z.infolist() if i.filename.endswith(".csv") and i.file_size >= 1200]
    study1 = set(np.random.default_rng(STUDY1_SEED).permutation(len(infos))[:STUDY1_DRAWN].tolist())  # C8
    remaining = [k for k in range(len(infos)) if k not in study1]
    _log(f"{len(infos)} files, {len(study1)} used in Study 1, {len(remaining)} remaining")
    for k in np.random.default_rng(SEED).permutation(remaining):
        info = infos[k]
        n_drawn += 1
        d = pd.read_csv(io.BytesIO(z.read(info)))
        if len(d) < MIN_ROWS:
            continue
        d["user"] = os.path.basename(info.filename)[:-4]
        frames.append(d)
        if len(frames) >= TARGET:
            break
_log(f"drawn {n_drawn}, kept {len(frames)}")

raw = pd.concat(frames, ignore_index=True).join(key, on="question_id", how="inner")
df = pd.DataFrame({"user": raw["user"], "order": raw["timestamp"], "skill": raw["skill"],
                   "correct": (raw["user_answer"] == raw["correct_answer"]).astype(int),
                   "rt": pd.to_numeric(raw["elapsed_time"], errors="coerce") / 1000.0})
df["order"] = df["order"].astype("int64") * 1000 + df.groupby("user").cumcount()

study1_users = set(pd.read_csv(os.path.join(out_dir, "ednet_learner_measures.csv"), usecols=[0]).iloc[:, 0].astype(str))
overlap = len(set(df["user"].unique()) & study1_users)

post, k = prepare(df); _log(f"post rows {len(post)}, learners {post['user'].nunique()}")
E1 = e1(post)
seq = mastery_sequences(post); _log(f"sequences {len(seq)}")
learner = pd.concat([k, E1], axis=1, join="inner").dropna()  # C9
learner["zE1"], learner["zK"] = zscore(learner["E1"]), zscore(learner["K"])

res = {"dataset": "EdNet-KT1 fresh sample (seed 2027, Study 1 files excluded)",
       "sampling": {"files_drawn": n_drawn, "learners_kept": len(frames), "rows": int(len(df)),
                    "overlap_with_study1_learners": overlap},
       "n_learners_eligible": int(post["user"].nunique()), "n_learners_with_E1_and_K": int(len(learner)),
       "descriptives": learner[["K", "E1"]].describe().round(4).to_dict()}
res["H1_cox"] = cox_x(seq[seq["user"].isin(learner.index)], learner, ["zE1", "zK"]); _log("H1 done")
odd, even = post[post["pidx"] % 2 == 1], post[post["pidx"] % 2 == 0]
res["H2_split_half_E1"] = split_half_r(e1(odd), e1(even)); _log("H2 done")

with open(os.path.join(out_dir, "h1h2_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
