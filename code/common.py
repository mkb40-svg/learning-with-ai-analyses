"""Shared measures and tests for the secondary analysis (see ../analysis_plan.md).

Every function takes a long table with one row per opportunity and the columns:
    user, order, skill, correct (0/1), rt (seconds, may be NaN)
and follows the operational definitions fixed in the analysis plan (v1.0, 2026-11-20).

Clarifications made BEFORE running on any data (reported as such in the write-up):
  C1  Learner-level mastery rate: a sequence (learner x skill) that never reaches mastery
      contributes 1 / (n_opportunities + 1), a conservative bound; mastered sequences contribute
      1 / opportunities_to_mastery.
  C2  For the ratio model (SH3) E is shifted to be non-negative: E+ = E - min(E), and c >= 0.
  C3  Cox models are stratified by skill (instead of a random effect for skill), with robust
      standard errors clustered by learner.
"""
import numpy as np
import pandas as pd
from scipy import stats, optimize

BASELINE = 10          # first opportunities used for K and excluded from outcomes
MIN_POST = 30          # minimum opportunities after the baseline window
RT_MIN, RT_MAX = 1.0, 600.0
MIN_PAIRS = 5          # minimum pairs for E1 / E2 to be defined


def prepare(df):
    df = df.sort_values(["user", "order"]).reset_index(drop=True)
    df["idx"] = df.groupby("user").cumcount()
    df["prev_correct"] = df.groupby("user")["correct"].shift(1)
    rt = df["rt"].where((df["rt"] >= RT_MIN) & (df["rt"] <= RT_MAX))
    df["logrt"] = np.log(rt)
    k = df[df["idx"] < BASELINE].groupby("user")["correct"].mean().rename("K")
    post = df[df["idx"] >= BASELINE].copy()
    post["pidx"] = post["idx"] - BASELINE
    n_post = post.groupby("user").size()
    keep = n_post[n_post >= MIN_POST].index
    post = post[post["user"].isin(keep)].copy()
    # next opportunity of the same skill (for E2 and mastery)
    post = post.sort_values(["user", "skill", "order"])
    post["next_same_skill_correct"] = post.groupby(["user", "skill"])["correct"].shift(-1)
    post = post.sort_values(["user", "order"])
    return post, k.loc[keep]


def e1(post):
    g = post.dropna(subset=["logrt", "prev_correct"])
    after_err = g[g["prev_correct"] == 0].groupby("user")["logrt"].agg(["median", "size"])
    after_ok = g[g["prev_correct"] == 1].groupby("user")["logrt"].agg(["median", "size"])
    j = after_err.join(after_ok, lsuffix="_err", rsuffix="_ok", how="inner")
    j = j[(j["size_err"] >= MIN_PAIRS) & (j["size_ok"] >= MIN_PAIRS)]
    return (j["median_err"] - j["median_ok"]).rename("E1")


def e2(post):
    err_rate = 1 - post.groupby("user")["correct"].mean()
    g = post[(post["correct"] == 0) & post["next_same_skill_correct"].notna()]
    agg = g.groupby("user")["next_same_skill_correct"].agg(["mean", "size"])
    agg = agg[agg["size"] >= MIN_PAIRS]
    p_err_after_err = 1 - agg["mean"]
    return (p_err_after_err - err_rate.loc[agg.index]).rename("E2")


def zscore(s):
    return (s - s.mean()) / s.std(ddof=1)


def composite(e1s, e2s):
    j = pd.concat([e1s, e2s], axis=1, join="inner")
    return ((zscore(j["E1"]) + zscore(j["E2"])) / 2).rename("E"), j


def mastery_sequences(post):
    """One row per learner x skill with >= 3 opportunities: opportunities to 3-in-a-row."""
    rows = []
    p = post.dropna(subset=["skill"]).sort_values(["user", "skill", "order"])  # rows without a skill cannot form a sequence
    users = p["user"].to_numpy(); skills = p["skill"].to_numpy(); corr = p["correct"].to_numpy()
    n = len(p); i = 0
    while i < n:
        j = i + 1
        while j < n and users[j] == users[i] and skills[j] == skills[i]:
            j += 1
        seq = corr[i:j]
        if len(seq) >= 3:
            streak, hit = 0, None
            for t, c in enumerate(seq, start=1):
                streak = streak + 1 if c == 1 else 0
                if streak == 3:
                    hit = t
                    break
            rows.append((users[i], skills[i], len(seq), hit if hit else len(seq), 1 if hit else 0))
        i = j
    return pd.DataFrame(rows, columns=["user", "skill", "n_opps", "duration", "event"])


def learner_rate(seq):
    r = np.where(seq["event"] == 1, 1.0 / seq["duration"], 1.0 / (seq["n_opps"] + 1))  # C1
    return pd.Series(r, index=seq.index).groupby(seq["user"]).mean().rename("rate")


def split_half(post):
    """SH1: E composite on odd vs even post-baseline opportunities."""
    out = {}
    for name, part in (("odd", post[post["pidx"] % 2 == 1]), ("even", post[post["pidx"] % 2 == 0])):
        out[name] = (e1(part), e2(part))
    eo, _ = composite(*out["odd"])
    ee, _ = composite(*out["even"])
    j = pd.concat([eo.rename("odd"), ee.rename("even")], axis=1, join="inner").dropna()
    r = stats.pearsonr(j["odd"], j["even"])[0]
    rho = stats.spearmanr(j["odd"], j["even"])[0]
    rng = np.random.default_rng(2026)
    boots = []
    a, b = j["odd"].to_numpy(), j["even"].to_numpy()
    for _ in range(1000):
        ix = rng.integers(0, len(a), len(a))
        boots.append(np.corrcoef(a[ix], b[ix])[0, 1])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    sb = lambda x: 2 * x / (1 + x)
    # same for each component separately
    comp = {}
    for k_ in ("E1", "E2"):
        idx_ = 0 if k_ == "E1" else 1
        jj = pd.concat([out["odd"][idx_].rename("odd"), out["even"][idx_].rename("even")], axis=1, join="inner").dropna()
        comp[k_] = {"n": len(jj), "r": float(stats.pearsonr(jj["odd"], jj["even"])[0])}
    return {"n": len(j), "pearson_r": float(r), "spearman_rho": float(rho),
            "r_95ci": [float(lo), float(hi)], "spearman_brown": float(sb(r)),
            "spearman_brown_95ci": [float(sb(lo)), float(sb(hi))], "components": comp,
            "meets_threshold_r_ge_0.30": bool(r >= 0.30)}


def cox(seq, learner):
    """SH2 primary: Cox model of opportunities to mastery, stratified by skill, clustered by learner."""
    from statsmodels.duration.hazard_regression import PHReg
    d = seq.merge(learner[["zE", "zK"]], left_on="user", right_index=True, how="inner")
    m = PHReg(d["duration"].to_numpy(float), d[["zE", "zK"]].to_numpy(float),
              status=d["event"].to_numpy(int), strata=pd.factorize(d["skill"])[0])
    res = m.fit()
    # cluster-robust (learner) sandwich computed by hand: statsmodels' built-in robust option
    # returned NaN because strata with a single sequence give NaN score residuals (set to 0 here).
    sr = np.nan_to_num(np.asarray(res.score_residuals, dtype=float))
    g = pd.factorize(d["user"])[0]
    S = np.zeros((g.max() + 1, sr.shape[1]))
    np.add.at(S, g, sr)
    naive = np.asarray(res.cov_params())
    robust = naive @ (S.T @ S) @ naive
    se = np.sqrt(np.diag(robust)); b = np.asarray(res.params)
    z = b / se; p = 2 * stats.norm.sf(np.abs(z))
    lo, hi = np.exp(b - 1.96 * se), np.exp(b + 1.96 * se)
    return {"n_sequences": int(len(d)), "n_learners": int(d["user"].nunique()),
            "mastered_share": float(d["event"].mean()),
            "HR_per_SD_E": float(np.exp(b[0])), "HR_E_95ci": [float(lo[0]), float(hi[0])], "p_E": float(p[0]),
            "HR_per_SD_K": float(np.exp(b[1])), "HR_K_95ci": [float(lo[1]), float(hi[1])], "p_K": float(p[1]),
            "model_based_p_E": float(res.pvalues[0])}


def exploratory_components(learner):
    """NOT pre-registered: E1 and E2 entered separately (reported as exploratory)."""
    import statsmodels.api as sm
    d = learner.copy()
    d["zE1"], d["zE2"] = zscore(d["E1"]), zscore(d["E2"])
    res = sm.OLS(d["zrate"], sm.add_constant(d[["zE1", "zE2", "zK"]])).fit(cov_type="HC3")
    ci = res.conf_int()
    return {k: {"beta_std": float(res.params[k]), "95ci": [float(ci.loc[k, 0]), float(ci.loc[k, 1])],
                "p": float(res.pvalues[k])} for k in ("zE1", "zE2", "zK")} | {"r2": float(res.rsquared)}


def ols_check(learner):
    import statsmodels.api as sm
    X = sm.add_constant(learner[["zE", "zK"]])
    res = sm.OLS(learner["zrate"], X).fit(cov_type="HC3")
    ci = res.conf_int()
    return {"n": int(len(learner)), "beta_E_std": float(res.params["zE"]),
            "beta_E_95ci": [float(ci.loc["zE", 0]), float(ci.loc["zE", 1])], "p_E": float(res.pvalues["zE"]),
            "beta_K_std": float(res.params["zK"]), "p_K": float(res.pvalues["zK"]), "r2": float(res.rsquared)}


def ratio_vs_additive(learner, folds=10, seed=2026):
    """SH3: 10-fold CV RMSE of Va = b*K/(1+c*E+) vs Va = a + b1*K + b2*E (one row per learner)."""
    d = learner[["rate", "K", "E"]].dropna().copy()
    d["Ep"] = d["E"] - d["E"].min()  # C2
    rng = np.random.default_rng(seed)
    fold = rng.permutation(len(d)) % folds
    se_r, se_a = [], []
    for f in range(folds):
        tr, te = d[fold != f], d[fold == f]
        def resid(p, x):
            return p[0] * x["K"].to_numpy() / (1 + p[1] * x["Ep"].to_numpy()) - x["rate"].to_numpy()
        fit = optimize.least_squares(resid, x0=[tr["rate"].mean() / max(tr["K"].mean(), 1e-6), 0.1],
                                     bounds=([0, 0], [np.inf, 100]), args=(tr,))
        se_r.append(resid(fit.x, te) ** 2)
        X = np.column_stack([np.ones(len(tr)), tr["K"], tr["E"]])
        beta = np.linalg.lstsq(X, tr["rate"].to_numpy(), rcond=None)[0]
        Xt = np.column_stack([np.ones(len(te)), te["K"], te["E"]])
        se_a.append((Xt @ beta - te["rate"].to_numpy()) ** 2)
    full = optimize.least_squares(lambda p: p[0] * d["K"].to_numpy() / (1 + p[1] * d["Ep"].to_numpy()) - d["rate"].to_numpy(),
                                  x0=[1, 0.1], bounds=([0, 0], [np.inf, 100]))
    rm = lambda s: float(np.sqrt(np.mean(np.concatenate(s))))
    return {"n": int(len(d)), "cv_rmse_ratio": rm(se_r), "cv_rmse_additive": rm(se_a),
            "ratio_better": bool(rm(se_r) < rm(se_a)), "ratio_params_b_c": [float(x) for x in full.x]}


def practice_curves(seq_post):
    """Reference: population error rate by opportunity number within skill, power vs exponential."""
    p = seq_post.sort_values(["user", "skill", "order"]).copy()
    p["k"] = p.groupby(["user", "skill"]).cumcount() + 1
    curve = p[p["k"] <= 20].groupby("k")["correct"].agg(["mean", "size"])
    k = curve.index.to_numpy(float); err = 1 - curve["mean"].to_numpy()
    w = np.sqrt(curve["size"].to_numpy(float))
    pw = optimize.curve_fit(lambda k, a, b: a * k ** (-b), k, err, p0=[err[0], 0.3], sigma=1 / w, maxfev=20000)[0]
    ex = optimize.curve_fit(lambda k, a, b, c: a * np.exp(-b * k) + c, k, err, p0=[err[0], 0.2, err[-1]], sigma=1 / w, maxfev=20000)[0]
    rm = lambda pred: float(np.sqrt(np.average((pred - err) ** 2, weights=curve["size"])))
    return {"rmse_power": rm(pw[0] * k ** (-pw[1])), "rmse_exponential": rm(ex[0] * np.exp(-ex[1] * k) + ex[2]),
            "error_rate_by_opportunity": [round(float(x), 4) for x in err]}


def _log(msg):
    import time
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def run_all(df, label):
    _log(f"start {label}: {len(df)} rows")
    post, k = prepare(df); _log(f"prepare done: {len(post)} post rows, {post['user'].nunique()} learners")
    e1s, e2s = e1(post), e2(post); _log(f"E1 n={len(e1s)}, E2 n={len(e2s)}")
    E, comps = composite(e1s, e2s)
    seq = mastery_sequences(post); _log(f"mastery sequences: {len(seq)}")
    rate = learner_rate(seq)
    learner = pd.concat([k, E, comps, rate], axis=1, join="inner").dropna()
    learner["zE"], learner["zK"], learner["zrate"] = zscore(learner["E"]), zscore(learner["K"]), zscore(learner["rate"])
    res = {"dataset": label,
           "n_rows_post": int(len(post)), "n_learners_eligible": int(post["user"].nunique()),
           "n_learners_with_E_and_rate": int(len(learner)),
           "E1_E2_correlation": float(stats.pearsonr(learner["E1"], learner["E2"])[0]),
           "descriptives": learner[["K", "E1", "E2", "rate"]].describe().round(4).to_dict()}
    res["SH1_split_half"] = split_half(post); _log("SH1 done")
    res["SH2_ols_check"] = ols_check(learner); _log("SH2 OLS done")
    res["SH3_ratio_vs_additive"] = ratio_vs_additive(learner); _log("SH3 done")
    res["reference_practice_curves"] = practice_curves(post); _log("practice curves done")
    res["SH2_cox"] = cox(seq[seq["user"].isin(learner.index)], learner); _log("SH2 Cox done")
    res["EXPLORATORY_components_not_preregistered"] = exploratory_components(learner)
    return res, learner
