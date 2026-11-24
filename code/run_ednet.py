"""G3 adult learners: EdNet-KT1 (TOEIC, Santa app).

Usage: python -I run_ednet.py <EdNet-KT1.zip> <EdNet-Contents.zip> <results_dir>

Clarifications made before running:
  C5  The skill of a question is its first listed tag in contents/questions.csv.
  C6  Sampling: learners are drawn in random order (seed 2026) from files large enough to hold
      >= 40 responses; each drawn learner is kept if eligible (>= 10 baseline + >= 30 later
      responses) until 20,000 eligible learners are reached. The archive is never fully extracted.
  C7  Correctness = user_answer equals the question's correct_answer; rt = elapsed_time / 1000.
"""
import io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import run_all  # noqa: E402

kt1_zip, contents_zip, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
TARGET, MIN_ROWS, SEED = 20000, 40, 2026

with zipfile.ZipFile(contents_zip) as zc:
    qname = [n for n in zc.namelist() if n.lower().endswith("questions.csv")][0]
    q = pd.read_csv(zc.open(qname))
q["skill"] = q["tags"].astype(str).str.split(";").str[0]
key = q.set_index("question_id")[["correct_answer", "skill"]]

frames, n_drawn = [], 0
with zipfile.ZipFile(kt1_zip) as z:
    infos = [i for i in z.infolist() if i.filename.endswith(".csv") and i.file_size >= 1200]
    order = np.random.default_rng(SEED).permutation(len(infos))
    for k in order:
        info = infos[k]
        n_drawn += 1
        d = pd.read_csv(io.BytesIO(z.read(info)))
        if len(d) < MIN_ROWS:
            continue
        d["user"] = os.path.basename(info.filename)[:-4]
        frames.append(d)
        if len(frames) >= TARGET:
            break

raw = pd.concat(frames, ignore_index=True)
raw = raw.join(key, on="question_id", how="inner")
df = pd.DataFrame({
    "user": raw["user"],
    "order": raw["timestamp"],
    "skill": raw["skill"],
    "correct": (raw["user_answer"] == raw["correct_answer"]).astype(int),
    "rt": pd.to_numeric(raw["elapsed_time"], errors="coerce") / 1000.0,
})
# keep within-user order stable for equal timestamps
df["order"] = df["order"].astype("int64") * 1000 + df.groupby("user").cumcount()

res, learner = run_all(df, "EdNet-KT1 (adult learners, TOEIC English)")
res["sampling"] = {"files_drawn": int(n_drawn), "learners_kept": len(frames), "rows": int(len(df))}
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "ednet_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
learner.to_csv(os.path.join(out_dir, "ednet_learner_measures.csv"))
print(json.dumps(res, indent=2, ensure_ascii=False))
