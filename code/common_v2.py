"""Helpers for analysis plan v2 (../analysis_plan_v2.md, amendment A2)."""
import numpy as np
import pandas as pd
from scipy import stats


def zscore(s):
    return (s - s.mean()) / s.std(ddof=1)


def cox_x(seq, learner, cols):
    """Cox model of opportunities to mastery, stratified by skill, learner-clustered sandwich SE.
    Same estimator as common.cox (Study 1), with the covariates named in `cols`."""
    from statsmodels.duration.hazard_regression import PHReg
    d = seq.merge(learner[cols], left_on="user", right_index=True, how="inner")
    m = PHReg(d["duration"].to_numpy(float), d[cols].to_numpy(float),
              status=d["event"].to_numpy(int), strata=pd.factorize(d["skill"])[0])
    res = m.fit()
    sr = np.nan_to_num(np.asarray(res.score_residuals, dtype=float))
    g = pd.factorize(d["user"])[0]
    S = np.zeros((g.max() + 1, sr.shape[1]))
    np.add.at(S, g, sr)
    naive = np.asarray(res.cov_params())
    robust = naive @ (S.T @ S) @ naive
    se = np.sqrt(np.diag(robust)); b = np.asarray(res.params)
    z = b / se
    out = {"n_sequences": int(len(d)), "n_learners": int(d["user"].nunique()),
           "mastered_share": float(d["event"].mean())}
    for i, c in enumerate(cols):
        out[c] = {"HR": float(np.exp(b[i])), "95ci": [float(np.exp(b[i] - 1.96 * se[i])), float(np.exp(b[i] + 1.96 * se[i]))],
                  "z": float(z[i]), "p_two_sided": float(2 * stats.norm.sf(abs(z[i]))),
                  "p_one_sided_HR_gt_1": float(stats.norm.sf(z[i])), "p_one_sided_HR_lt_1": float(stats.norm.cdf(z[i]))}
    return out


def demean(X, codes, tol=1e-10, maxit=500):
    """Absorb several sets of fixed effects by alternating projections."""
    X = X.astype(float).copy()
    counts = [np.bincount(c) for c in codes]
    for _ in range(maxit):
        old = X.copy()
        for c, n in zip(codes, counts):
            for j in range(X.shape[1]):
                X[:, j] -= (np.bincount(c, weights=X[:, j]) / n)[c]
        if np.max(np.abs(X - old)) < tol:
            break
    return X


def fe_lpm(df, y, xs, fes, cluster):
    """Linear probability model with absorbed fixed effects and CR1 cluster-robust SE."""
    d = df.dropna(subset=[y] + xs + fes + [cluster]).copy()
    codes = [pd.factorize(d[f])[0] for f in fes]
    M = demean(d[[y] + xs].to_numpy(float), codes)
    yy, X = M[:, 0], M[:, 1:]
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ yy
    u = yy - X @ b
    g = pd.factorize(d[cluster])[0]
    G = g.max() + 1
    S = np.zeros((G, X.shape[1]))
    np.add.at(S, g, X * u[:, None])
    n, k = len(d), X.shape[1] + sum(len(np.unique(c)) for c, f in zip(codes, fes) if f != cluster)
    adj = G / (G - 1) * (n - 1) / max(n - k, 1)
    V = adj * XtX_inv @ (S.T @ S) @ XtX_inv
    se = np.sqrt(np.diag(V))
    out = {"n_obs": int(n), "n_clusters": int(G), "outcome_mean": float(d[y].mean())}
    for i, x in enumerate(xs):
        t = b[i] / se[i]
        out[x] = {"b": float(b[i]), "se": float(se[i]), "95ci": [float(b[i] - 1.96 * se[i]), float(b[i] + 1.96 * se[i])],
                  "p_two_sided": float(2 * stats.t.sf(abs(t), G - 1))}
    return out


def split_half_r(a, b, threshold=0.30, seed=2027, n_boot=1000):
    j = pd.concat([a.rename("odd"), b.rename("even")], axis=1, join="inner").dropna()
    r = float(stats.pearsonr(j["odd"], j["even"])[0])
    rng = np.random.default_rng(seed)
    x, y = j["odd"].to_numpy(), j["even"].to_numpy()
    boots = [np.corrcoef(x[ix], y[ix])[0, 1] for ix in (rng.integers(0, len(x), len(x)) for _ in range(n_boot))]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    zstat = (np.arctanh(r) - np.arctanh(threshold)) * np.sqrt(len(j) - 3)
    sb = lambda v: 2 * v / (1 + v)
    return {"n": int(len(j)), "r": r, "95ci": [float(lo), float(hi)], "spearman_brown": float(sb(r)),
            "meets_threshold": bool(r >= threshold), "p_one_sided_rho_gt_threshold": float(stats.norm.sf(zstat))}


def holm(pvals):
    """pvals: dict name -> p. Returns dict name -> Holm-adjusted p."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out
