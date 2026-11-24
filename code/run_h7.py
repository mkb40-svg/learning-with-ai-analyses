"""H7 (plan v2, amendment A5): "I give up after making mistakes" and mathematics, PISA 2022 Malaysia.

Usage: python -I run_h7.py <CY08MSP_STU_QQQ.SAV> <results_dir>
"""
import json, os, sys
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

sav, out_dir = sys.argv[1], sys.argv[2]
PV = [f"PV{i}MATH" for i in range(1, 11)]
RW = [f"W_FSTURWT{i}" for i in range(1, 81)]
cols = ["CNT", "ST307Q06JA", "ESCS", "ST004D01T", "W_FSTUWT"] + PV + RW
df, _ = pyreadstat.read_sav(sav, usecols=cols, apply_value_formats=False)
d = df[df["CNT"] == "MYS"].copy()
n_mys = len(d)
d["giveup"] = d["ST307Q06JA"].where(d["ST307Q06JA"].between(1, 5))
d["male"] = (d["ST004D01T"] == 2).astype(float).where(d["ST004D01T"].isin([1, 2]))
d["ESCS"] = d["ESCS"].where(d["ESCS"].abs() < 90)
d = d.dropna(subset=["giveup", "ESCS", "male", "W_FSTUWT"])
X = np.column_stack([np.ones(len(d)), d[["giveup", "ESCS", "male"]].to_numpy(float)])
names = ["const", "giveup", "ESCS", "male"]


def wls(y, w):
    Xw = X * w[:, None]
    return np.linalg.solve(X.T @ Xw, Xw.T @ y)


est, samp_var = [], []
for pv in PV:
    y = d[pv].to_numpy(float)
    b = wls(y, d["W_FSTUWT"].to_numpy(float))
    reps = np.array([wls(y, d[r].to_numpy(float)) for r in RW])
    est.append(b); samp_var.append(((reps - b) ** 2).sum(axis=0) / 20.0)  # Fay k = 0.5
est, samp_var = np.array(est), np.array(samp_var)
M = len(PV)
b_bar = est.mean(axis=0)
U = samp_var.mean(axis=0)
Bv = est.var(axis=0, ddof=1)
T = U + (1 + 1 / M) * Bv
se = np.sqrt(T)
r = (1 + 1 / M) * Bv / U
dfr = (M - 1) * (1 + 1 / r) ** 2
t = b_bar / se
p = 2 * stats.t.sf(np.abs(t), dfr)

w = d["W_FSTUWT"].to_numpy(float)
dist = d.groupby("giveup")["W_FSTUWT"].sum() / w.sum()
math_mean = float(np.average(d[PV].mean(axis=1), weights=w))
sd_math = float(np.sqrt(np.average((d[PV].mean(axis=1) - math_mean) ** 2, weights=w)))
res = {"dataset": "PISA 2022, Malaysia", "n_students_MYS": int(n_mys), "n_analysed": int(len(d)),
       "weighted_mean_math": math_mean, "weighted_sd_math_mean_of_PVs": sd_math,
       "weighted_distribution_giveup_1to5": {str(int(k)): round(float(v), 4) for k, v in dist.items()},
       "H7": {n: {"b": float(b_bar[i]), "se": float(se[i]), "95ci": [float(b_bar[i] - 1.96 * se[i]), float(b_bar[i] + 1.96 * se[i])],
                  "p_two_sided": float(p[i])} for i, n in enumerate(names)}}
res["H7_b_giveup_in_SD_of_math_per_step"] = float(b_bar[1] / sd_math)
with open(os.path.join(out_dir, "h7_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
