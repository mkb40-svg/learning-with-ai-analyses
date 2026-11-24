"""H8 (exploratory; plan v2, amendment A6): substitution vs complementary ChatGPT use, Malaysian students.

Usage: python -I run_h8.py <final_dataset.xlsx> <results_dir>
"""
import json, os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common_v2 import fe_lpm  # noqa: E402

xlsx, out_dir = sys.argv[1], sys.argv[2]
d = pd.read_excel(xlsx, usecols=["Q4", "Q13a", "Q15", "Q18a", "Q18i", "Q29e"])
d = d[d["Q13a"] == 1].dropna(subset=["Q4", "Q15", "Q18a", "Q18i", "Q29e"]).copy()
d["rel_sub"] = d["Q18a"] - d["Q18i"]
d["mean_use"] = (d["Q18a"] + d["Q18i"]) / 2
m = d[d["Q4"] == "Malaysia"]
res = {"dataset": "Global ChatGPT Student Survey wave 2 (Mendeley nv2343nwsb v2)", "n_malaysia_analysed": int(len(m)),
       "descriptives_malaysia": m[["Q18a", "Q18i", "rel_sub", "Q15", "Q29e"]].describe().round(3).to_dict()}
fit = sm.OLS(m["Q29e"], sm.add_constant(m[["rel_sub", "mean_use", "Q15"]])).fit(cov_type="HC3")
ci = fit.conf_int()
res["H8_malaysia_ols_hc3"] = {k: {"b": float(fit.params[k]), "95ci": [float(ci.loc[k, 0]), float(ci.loc[k, 1])], "p_two_sided": float(fit.pvalues[k])}
                             for k in ["rel_sub", "mean_use", "Q15"]} | {"r2": float(fit.rsquared)}
res["CONTEXT_all_countries_country_fe"] = fe_lpm(d, "Q29e", ["rel_sub", "mean_use", "Q15"], ["Q4"], "Q4") | {
    "n_countries": int(d["Q4"].nunique())}
with open(os.path.join(out_dir, "h8_results.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print(json.dumps(res, indent=2, ensure_ascii=False))
