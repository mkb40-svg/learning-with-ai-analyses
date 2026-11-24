"""EdNet-KT3 sample and response parser, identical to run_h5.py (seed 2028), as a reusable module."""
import io, os, zipfile
import numpy as np
import pandas as pd

TARGET, MIN_RESP, SEED, WINDOW_MS = 20000, 40, 2028, 300_000
key = None


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


def load_sample(kt3_zip, contents_zip, log=print):
    global key
    with zipfile.ZipFile(contents_zip) as zc:
        q = pd.read_csv(zc.open([n for n in zc.namelist() if n.endswith("questions.csv") and "__MACOSX" not in n][0]))
    q["tag"] = q["tags"].astype(str).str.split(";").str[0]
    key = q.set_index("question_id")[["bundle_id", "explanation_id", "correct_answer", "tag"]]
    frames, n_drawn = [], 0
    with zipfile.ZipFile(kt3_zip) as z:
        infos = [i for i in z.infolist() if i.filename.startswith("KT3/u") and i.filename.endswith(".csv") and i.file_size >= 3000]
        for k in np.random.default_rng(SEED).permutation(len(infos)):
            info = infos[k]; n_drawn += 1
            r = responses(pd.read_csv(io.BytesIO(z.read(info)), dtype={"user_answer": str}))
            if r is None or len(r) < MIN_RESP:
                continue
            r["user"] = os.path.basename(info.filename)[:-4]
            frames.append(r)
            if len(frames) % 5000 == 0:
                log(f"kept {len(frames)} / drawn {n_drawn}")
            if len(frames) >= TARGET:
                break
    return pd.concat(frames, ignore_index=True), n_drawn
