"""Final figures for Preprint 3, drawn from results/h6_results.json, h7_results.json and p3_robust.json.

Usage: python -I make_figures_p3.py <results_dir> <figure_dir>
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

rd, fd = sys.argv[1:3]
plt = setup()
L = lambda f: json.load(open(os.path.join(rd, f), encoding="utf-8"))
h6, rob = L("h6_results.json"), L("p3_robust.json")

# Figure 1: PISA mathematics by response to "I give up after making mistakes"
fm = rob["PISA_figure_means"]
labels = ["Strongly\ndisagree", "Disagree", "Neither agree\nnor disagree", "Agree", "Strongly\nagree"]
vals = list(fm.values())
fig, ax = plt.subplots(figsize=(6.3, 2.9))
x = np.arange(5)
ax.errorbar(x, [v["mean"] for v in vals], yerr=[v["ci95"] for v in vals], fmt="o", color=BLUE, capsize=3, ms=6)
for xi, v in zip(x, vals):
    ax.text(xi + 0.12, v["mean"], f"{v['mean']:.0f}", va="center", fontsize=8, color=DARK)
    ax.text(xi, 345, f"{100 * v['weighted_share']:.0f}% of pupils\n(n = {v['n']:,})", ha="center", va="bottom", fontsize=7, color=GREY)
ax.set_xticks(x, labels, fontsize=8)
ax.set_ylim(340, 440)
ax.set_ylabel("Mathematics score\n(weighted mean, 95% CI)")
fig.savefig(os.path.join(fd, "fig_p3_pisa.png"))
plt.close(fig)

# Figure 2: H6 estimates with and without the submissions control
rows = [("Reviewed within 24 h: confirmatory H6", h6["H6_fe"]["review_share"], BLUE, "s"),
        ("  + control for number of quiz submissions", rob["SED_H6_plus_submissions_control"]["review_share"], GREY, "o"),
        ("  only courses where the review share varies", rob["SED_H6_courses_with_variation"]["review_share"], GREY, "o"),
        ("Returned to the attempt after > 60 s (exploratory)", h6["EXPLORATORY_A4_returning_review"]["returning_share"], DARK, "o"),
        ("  + control for number of quiz submissions", rob["SED_returning_plus_submissions_control"]["returning_share"], GREY, "o")]
fig, ax = plt.subplots(figsize=(6.3, 2.5))
y = np.arange(len(rows))[::-1]
for yi, (lab, r, col, mk) in zip(y, rows):
    b, lo, hi = r["b"], r["95ci"][0], r["95ci"][1]
    ax.errorbar(b, yi, xerr=[[b - lo], [hi - b]], fmt=mk, color=col, capsize=3, ms=5)
    ax.text(3.7, yi, f"{b:+.2f} ({lo:+.2f} to {hi:+.2f}), p = {r['p_two_sided']:.2g}", va="center", fontsize=7.5)
ax.axvline(0, color="#999999", lw=1, ls="--")
ax.set_yticks(y, [r[0] for r in rows], fontsize=8)
ax.set_xlim(-2, 3.6)
ax.set_xlabel("Difference in final course mark (0–100) for a share of 1 vs 0, within course (95% CI)")
fig.savefig(os.path.join(fd, "fig_p3_sed.png"))
plt.close(fig)
print("figures written")
