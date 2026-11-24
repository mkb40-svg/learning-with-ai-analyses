"""H5 (plan v2, amendment A2: C13): explanation viewing after an incorrect answer, EdNet-KT3.

Usage: python -I run_h5.py <EdNet-KT3.zip> <EdNet-Contents.zip> <results_dir>
"""
import io, json, os, sys, zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import prepare, _log  # noqa: E402
from common_v2 import fe_lpm  # noqa: E402

kt3_zip, contents_zip, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
TARGET, MIN_RESP, SEED, WINDOW_MS = 20000, 40, 2028, 300_000

with zipfile.ZipFile(contents_zip) as zc:
    q = pd.read_csv(zc.open([n for n in zc.namelist() if n.endswith("questions.csv") and "__MACOSX" not in n][0]))
q["tag"] = q["tags"].astype(str).str.split(";").str[0]
key = q.set_index("question_id")[["bundle_id", "explanation_id", "correct_answer", "tag"]]


def responses(d):
    d = d.sort_values("timestamp", kind="stable")
    resp = d[(d["action_type"] == "respond") & d["item_id"].str.startswith("q")][["timestamp", "item_id", "user_answer", "source"]]
    subs = d[(d["action_type"] == "submit") & d["item_id"].str.startswith("b")][["timestamp", "item_id"]]
    if resp.empty or subs.empty:
        return None
    subs = subs.rename(columns={"item_id": "sub_bundle"}); subs["sub_ts"] = subs["timestamp"]
    r = pd.merge_asof(resp, subs, on="timestamp", direction="forward").dropna(subset=["sub_ts"])
    r["sub_ts"] = r["sub_ts"].astype("int64")
    r = r.join(key, on="item_id", how="inner")
    r = r[r["bundle_id"] == r["sub_bundle"]]
    r = r.drop_duplicates(subset=["item_id", "sub_ts"], keep="last")  # last answer before submit
    r["correct"] = (r["user_answer"] == r["correct_answer"]).astype(int)
    ex = d[(d["action_type"] == "enter") & d["item_id"].str.startswith("e")][["timestamp", "item_id"]]
    r = r.sort_values("sub_ts")
    r["dwell"] = np.nan
    if ex.empty:
        r["viewed"] = 0
    else:
        ex = ex.rename(columns={"item_id": "explanation_id", "timestamp": "ex_ts"}).sort_values("ex_ts")
        ex["sub_ts"] = ex["ex_ts"]
        m = pd.merge_asof(r[["sub_ts", "explanation_id"]].reset_index(), ex, on="sub_ts", by="explanation_id",
                          direction="forward", tolerance=WINDOW_MS).set_index("index").reindex(r.index)
        r["viewed"] = m["ex_ts"].notna().astype(int).to_numpy()
        # A3(b): time on the explanation = enter -> next quit of the same explanation
        qu = d[(d["action_type"] == "quit") & d["item_id"].str.startswith("e")][["timestamp", "item_id"]]
        if not qu.empty:
            qu = qu.rename(columns={"item_id": "explanation_id", "timestamp": "quit_ts"}).sort_values("quit_ts")
            qu["ex_ts"] = qu["quit_ts"]
            v = m[["ex_ts", "explanation_id"]].dropna(subset=["ex_ts"]).copy()
            v["ex_ts"] = v["ex_ts"].astype("int64")
            v = pd.merge_asof(v.reset_index().sort_values("ex_ts"), qu, on="ex_ts", by="explanation_id",
                              direction="forward").set_index("index")
            r.loc[v.index, "dwell"] = (v["quit_ts"] - v["ex_ts"]) / 1000.0
    return r[["sub_ts", "item_id", "tag", "correct", "viewed", "dwell", "source"]]


frames, n_drawn = [], 0
with zipfile.ZipFile(kt3_zip) as z:
    infos = [i for i in z.infolist() if i.filename.startswith("KT3/u") and i.filename.endswith(".csv") and i.file_size >= 3000]
    _log(f"{len(infos)} candidate files")
    for k in np.random.default_rng(SEED).permutation(len(infos)):
        info = infos[k]; n_drawn += 1
        r = responses(pd.read_csv(io.BytesIO(z.read(info)), dtype={"user_answer": str}))
        if r is None or len(r) < MIN_RESP:
            continue
        r["user"] = os.path.basename(info.filename)[:-4]
        frames.append(r)
        if len(frames) % 2000 == 0:
            _log(f"kept {len(frames)} / drawn {n_drawn}")
        if len(frames) >= TARGET:
            break

raw = pd.concat(frames, ignore_index=True)
df = pd.DataFrame({"user": raw["user"], "skill": raw["tag"], "correct": raw["correct"], "rt": np.nan,
                   "viewed": raw["viewed"], "dwell": raw["dwell"], "source": raw["source"],
                   "order": raw["sub_ts"].astype("int64") * 1000 + raw.groupby("user").cumcount()})
post, _ = prepare(df); _log(f"post rows {len(post)}, learners {post['user'].nunique()}")
err = post[(post["correct"] == 0)].dropna(subset=["next_same_skill_correct"])
res = {"dataset": "EdNet-KT3 (seed 2028 sample)", "sampling": {"files_drawn": n_drawn, "learners_kept": len(frames), "responses": int(len(df))},
       "n_learners_eligible": int(post["user"].nunique()), "n_incorrect_with_next_same_tag": int(len(err)),
       "share_incorrect_followed_by_explanation": float(err["viewed"].mean()),
       "share_all_post_responses_followed_by_explanation": float(post["viewed"].mean())}
res["viewed_share_by_source_incorrect"] = err.groupby("source")["viewed"].agg(["mean", "size"]).round(4).to_dict()
res["H5_lpm"] = fe_lpm(err, "next_same_skill_correct", ["viewed"], ["user", "skill"], "user"); _log("H5 done")
res["EXPLORATORY_A3a_source_fixed_effect"] = fe_lpm(err, "next_same_skill_correct", ["viewed"], ["user", "skill", "source"], "user")
dw = err[(err["viewed"] == 1) & err["dwell"].between(1, 600)].copy()
dw["zlogdwell"] = (np.log(dw["dwell"]) - np.log(dw["dwell"]).mean()) / np.log(dw["dwell"]).std()
res["EXPLORATORY_A3b_dwell_descriptives_seconds"] = dw["dwell"].describe().round(2).to_dict()
res["EXPLORATORY_A3b_time_on_explanation"] = fe_lpm(dw, "next_same_skill_correct", ["zlogdwell"], ["user", "skill"], "user")
_log("exploratory done")
with open(os.path.join(out_dir, "h5_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
