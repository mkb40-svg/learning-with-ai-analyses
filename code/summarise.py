"""SH4: compare and pool the effect of E across groups; write results/summary.md.

Usage: python -I summarise.py <results_dir>
"""
import json, math, os, sys

rd = sys.argv[1]
files = [("School pupils (ASSISTments)", "assistments_results.json"),
         ("Adult learners (EdNet)", "ednet_results.json")]
R = [(name, json.load(open(os.path.join(rd, f), encoding="utf-8"))) for name, f in files]


def dl_pool(est, se):
    w = [1 / s ** 2 for s in se]
    fe = sum(wi * e for wi, e in zip(w, est)) / sum(w)
    q = sum(wi * (e - fe) ** 2 for wi, e in zip(w, est))
    df = len(est) - 1
    c = sum(w) - sum(wi ** 2 for wi in w) / sum(w)
    tau2 = max(0.0, (q - df) / c) if c > 0 else 0.0
    wr = [1 / (s ** 2 + tau2) for s in se]
    re = sum(wi * e for wi, e in zip(wr, est)) / sum(wr)
    se_re = math.sqrt(1 / sum(wr))
    i2 = max(0.0, (q - df) / q) if q > 0 else 0.0
    return re, se_re, q, i2, tau2


# Cox log hazard ratios per SD of E
est, se = [], []
for _, r in R:
    c = r["SH2_cox"]
    b = math.log(c["HR_per_SD_E"])
    s = (math.log(c["HR_E_95ci"][1]) - math.log(c["HR_E_95ci"][0])) / (2 * 1.96)
    est.append(b); se.append(s)
re, se_re, q, i2, tau2 = dl_pool(est, se)
pooled = {"HR_per_SD_E": math.exp(re), "95ci": [math.exp(re - 1.96 * se_re), math.exp(re + 1.96 * se_re)],
          "Q": q, "I2": i2, "tau2": tau2}

lines = ["# Secondary analysis: results summary", "",
         "Pre-registered plan: analysis_plan.md (v1.0, 2026-11-20). Clarifications C1-C7 are listed in the code.", "",
         "| Measure | " + " | ".join(n for n, _ in R) + " |", "| --- | " + " | ".join("---" for _ in R) + " |"]
def row(label, fn):
    lines.append(f"| {label} | " + " | ".join(fn(r) for _, r in R) + " |")
row("Learners analysed", lambda r: f"{r['n_learners_with_E_and_rate']:,}")
row("Opportunities after baseline", lambda r: f"{r['n_rows_post']:,}")
row("Correlation E1-E2", lambda r: f"{r['E1_E2_correlation']:.2f}")
row("SH1 split-half r of E composite (95% CI)", lambda r: f"{r['SH1_split_half']['pearson_r']:.2f} ({r['SH1_split_half']['r_95ci'][0]:.2f} to {r['SH1_split_half']['r_95ci'][1]:.2f})")
row("SH1 meets r >= 0.30", lambda r: "yes" if r["SH1_split_half"]["meets_threshold_r_ge_0.30"] else "no")
row("Split-half r of E1 alone / E2 alone", lambda r: f"{r['SH1_split_half']['components']['E1']['r']:.2f} / {r['SH1_split_half']['components']['E2']['r']:.2f}")
row("SH2 Cox HR per SD of E (95% CI)", lambda r: f"{r['SH2_cox']['HR_per_SD_E']:.3f} ({r['SH2_cox']['HR_E_95ci'][0]:.3f} to {r['SH2_cox']['HR_E_95ci'][1]:.3f})")
row("SH2 OLS std beta of E on mastery rate (95% CI)", lambda r: f"{r['SH2_ols_check']['beta_E_std']:.2f} ({r['SH2_ols_check']['beta_E_95ci'][0]:.2f} to {r['SH2_ols_check']['beta_E_95ci'][1]:.2f})")
row("SH3 CV RMSE ratio / additive", lambda r: f"{r['SH3_ratio_vs_additive']['cv_rmse_ratio']:.4f} / {r['SH3_ratio_vs_additive']['cv_rmse_additive']:.4f}")
row("Exploratory std beta E1 / E2", lambda r: f"{r['EXPLORATORY_components_not_preregistered']['zE1']['beta_std']:.2f} / {r['EXPLORATORY_components_not_preregistered']['zE2']['beta_std']:.2f}")
lines += ["", f"SH4 pooled HR per SD of E (random effects): {pooled['HR_per_SD_E']:.3f} "
          f"(95% CI {pooled['95ci'][0]:.3f} to {pooled['95ci'][1]:.3f}); Q = {pooled['Q']:.2f}, I2 = {100 * pooled['I2']:.0f}%.", "",
          "HR > 1 means faster mastery. The pre-registered direction for SH2 was HR < 1 (slower mastery with higher E)."]
open(os.path.join(rd, "summary.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
json.dump({"SH4_pooled_cox": pooled}, open(os.path.join(rd, "sh4_pooled.json"), "w"), indent=2)
print("\n".join(lines))
