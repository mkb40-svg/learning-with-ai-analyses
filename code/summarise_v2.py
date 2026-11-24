"""Summary of analysis plan v2 (H1-H8) with Holm correction (amendment A2). Writes results/summary_v2.md.

Usage: python -I summarise_v2.py <results_dir>
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common_v2 import holm  # noqa: E402

rd = sys.argv[1]
L = lambda f: json.load(open(os.path.join(rd, f), encoding="utf-8"))
h12, h34, h5, h6, h7, h8 = (L(f) for f in ["h1h2_results.json", "h3h4_results.json", "h5_results.json",
                                            "h6_results.json", "h7_results.json", "h8_results.json"])
rows = {}
c = h12["H1_cox"]["zE1"]
rows["H1"] = dict(test="E1 -> faster mastery (EdNet fresh sample)", est=f"HR {c['HR']:.3f} per SD ({c['95ci'][0]:.3f}-{c['95ci'][1]:.3f})",
                  n=f"{h12['H1_cox']['n_learners']:,} learners", p=c["p_one_sided_HR_gt_1"], sign_ok=c["HR"] > 1)
s = h12["H2_split_half_E1"]
rows["H2"] = dict(test="Split-half r of E1 >= 0.30", est=f"r {s['r']:.3f} ({s['95ci'][0]:.3f}-{s['95ci'][1]:.3f})",
                  n=f"{s['n']:,} learners", p=s["p_one_sided_rho_gt_threshold"], sign_ok=s["meets_threshold"])
c = h34["H3_cox"]["zHelp"]
rows["H3"] = dict(test="Help-first share -> slower mastery (ASSISTments)", est=f"HR {c['HR']:.3f} per SD ({c['95ci'][0]:.3f}-{c['95ci'][1]:.3f})",
                  n=f"{h34['H3_cox']['n_learners']:,} pupils", p=c["p_two_sided"], sign_ok=c["HR"] < 1)
c = h34["H4_lpm"]["bottom"]
rows["H4"] = dict(test="Answer shown -> next same-skill problem correct less often", est=f"{100*c['b']:+.1f} pp ({100*c['95ci'][0]:+.1f} to {100*c['95ci'][1]:+.1f})",
                  n=f"{h34['H4_lpm']['n_obs']:,} problems", p=c["p_two_sided"], sign_ok=c["b"] < 0)
c = h5["H5_lpm"]["viewed"]
rows["H5"] = dict(test="Explanation after error -> next same-tag answer correct (EdNet-KT3)", est=f"{100*c['b']:+.1f} pp ({100*c['95ci'][0]:+.1f} to {100*c['95ci'][1]:+.1f})",
                  n=f"{h5['H5_lpm']['n_obs']:,} errors", p=c["p_two_sided"], sign_ok=c["b"] > 0)
c = h6["H6_fe"]["review_share"]
rows["H6"] = dict(test="Quiz attempt review -> final course mark (UM Moodle)", est=f"{c['b']:+.2f} marks for 0->1 share ({c['95ci'][0]:+.2f} to {c['95ci'][1]:+.2f})",
                  n=f"{h6['n_pairs']:,} student-courses", p=c["p_two_sided"], sign_ok=c["b"] > 0)
c = h7["H7"]["giveup"]
rows["H7"] = dict(test="'I give up after mistakes' -> mathematics (PISA 2022 Malaysia)", est=f"{c['b']:+.1f} points per step ({c['95ci'][0]:+.1f} to {c['95ci'][1]:+.1f})",
                  n=f"{h7['n_analysed']:,} pupils", p=c["p_two_sided"], sign_ok=c["b"] < 0)
c = h8["H8_malaysia_ols_hc3"]["rel_sub"]
rows["H8"] = dict(test="Substitution vs study use of ChatGPT -> perceived critical thinking gain (exploratory)", est=f"{c['b']:+.3f} per point ({c['95ci'][0]:+.3f} to {c['95ci'][1]:+.3f})",
                  n=f"{h8['n_malaysia_analysed']:,} students", p=c["p_two_sided"], sign_ok=c["b"] < 0)

adj = holm({k: rows[k]["p"] for k in ["H1", "H2", "H3", "H4", "H5"]}) | holm({k: rows[k]["p"] for k in ["H6", "H7"]})
lines = ["# Secondary analysis v2: results summary", "",
         "Plan: analysis_plan_v2.md (v2.0 with amendments A1-A6, all recorded before the analysis they concern).",
         "Holm correction within H1-H5 and within H6-H7; H8 is exploratory (no correction).", "",
         "| | Hypothesis | Estimate (95% CI) | N | p | Holm p | Verdict |", "| --- | --- | --- | --- | --- | --- | --- |"]
for k, r in rows.items():
    hp = adj.get(k)
    if k == "H8":
        verdict = "exploratory: no association" if r["p"] >= 0.05 else ("exploratory: as predicted" if r["sign_ok"] else "exploratory: opposite")
    else:
        verdict = "supported" if (r["sign_ok"] and hp < 0.05) else "not supported"
    lines.append(f"| {k} | {r['test']} | {r['est']} | {r['n']} | {r['p']:.2g} | {'' if hp is None else f'{hp:.2g}'} | {verdict} |")
lines += ["", "## Exploratory checks", "",
          f"- H3 within learner: after a help-first problem the next same-skill problem is correct {100*h34['EXPLORATORY_H3_within_learner_next_correct_after_help_first']['help_first']['b']:+.1f} pp less often.",
          f"- H4 among incorrectly answered problems only: {100*h34['EXPLORATORY_H4_incorrect_only']['bottom']['b']:+.1f} pp.",
          f"- H5 with mode (source) fixed effect: {100*h5['EXPLORATORY_A3a_source_fixed_effect']['viewed']['b']:+.1f} pp (p = {h5['EXPLORATORY_A3a_source_fixed_effect']['viewed']['p_two_sided']:.2g}).",
          f"- H5 time on explanation (per SD of log seconds, among viewed errors): {100*h5['EXPLORATORY_A3b_time_on_explanation']['zlogdwell']['b']:+.1f} pp (p = {h5['EXPLORATORY_A3b_time_on_explanation']['zlogdwell']['p_two_sided']:.2g}; n = {h5['EXPLORATORY_A3b_time_on_explanation']['n_obs']:,}).",
          f"- H6 returning review (>60 s after submission): {h6['EXPLORATORY_A4_returning_review']['returning_share']['b']:+.2f} marks for 0->1 share (p = {h6['EXPLORATORY_A4_returning_review']['returning_share']['p_two_sided']:.2g}).",
          f"- H8 context, all {h8['CONTEXT_all_countries_country_fe']['n_countries']} countries: {h8['CONTEXT_all_countries_country_fe']['rel_sub']['b']:+.3f} (p = {h8['CONTEXT_all_countries_country_fe']['rel_sub']['p_two_sided']:.2g}).",
          "", "## Caveats", "",
          "- All data are observational: associations, not causal effects.",
          "- H3 is partly mechanical: ASSISTments scores a hint-first problem as incorrect (A2, C11).",
          "- H5 'viewing' is mostly automatic in practice mode (A3); H6 'review' is mostly an automatic Moodle redirect (A4).",
          f"- H7 uses {h7['n_analysed']:,} of {h7['n_students_MYS']:,} Malaysian pupils: the perseverance items were asked of a subsample.",
          "- H8 outcome is a perception of what ChatGPT can do, not a measured skill."]
open(os.path.join(rd, "summary_v2.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("\n".join(lines))
