"""Final figures for Preprint 1 from p1_robust.json, p1_robust_pes.json and p1_rapid.json (no recomputation).

Usage: python -I make_figures_p1.py <results_dir> <figure_dir>
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

rd, fd = sys.argv[1:3]
plt = setup()
L = lambda f: json.load(open(os.path.join(rd, f), encoding="utf-8"))
rob, pes, rap = L("p1_robust.json"), L("p1_robust_pes.json"), L("p1_rapid.json")

# Figure 1: cumulative mastery by E1 quartile (Study 2)
curves = rob["figure_cumulative_mastery"]
fig, ax = plt.subplots(figsize=(6.3, 2.9))
shades = ["#9ecae1", "#6baed6", "#2171b5", "#08306b"]
styles = ["--", "-", "-", "-"]
for (name, curve), c, ls in zip(curves.items(), shades, styles):
    ax.plot(range(1, 31), curve, color=c, lw=1.8, ls=ls, label=name)
ax.set_xlabel("Responses within a topic")
ax.set_ylabel("Topic sequences mastered\n(Kaplan–Meier)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}%"))
ax.set_xlim(1, 30)
ax.legend(title="Quartile of post-error slowing (E1)", fontsize=8, title_fontsize=8, loc="lower right")
fig.savefig(os.path.join(fd, "fig_p1_mastery_curves.png"))
plt.close(fig)

# Figure 2: hazard ratios across measures, samples and checks
s2, a1 = rob["EdNet_study2"], rob["ASSISTments_study1"]
rows = [
    ("EdNet adults, Study 2", None),
    ("Traditional E1 (confirmatory H1)", s2["E1_k3"]["zE1"]),
    ("Mastery = 2 in a row", s2["E1_k2"]["zE1"]),
    ("Mastery = 4 in a row", s2["E1_k4"]["zE1"]),
    ("E1 adjusted for item time demand", s2["E1_item_adjusted_k3"]["zE1"]),
    ("E1 + control for rapid responding", rap["EdNet_study2"]["cox_E1_K_rapid"]["zE1"]),
    ("E1, learners with ≤ 2% rapid responses", rap["EdNet_study2"]["cox_E1_K_learners_rapid_le_2pct"]["zE1"]),
    ("Robust slowing (after vs before the error)", pes["EdNet_study2"]["cox_robust_pes"]["zE1"]),
    ("EdNet adults, Study 1 sample", None),
    ("Traditional E1", rob["EdNet_study1"]["E1_k3"]["zE1"]),
    ("ASSISTments pupils", None),
    ("Traditional E1", a1["E1_k3"]["zE1"]),
    ("E1 + control for rapid responding", rap["ASSISTments"]["cox_E1_K_rapid"]["zE1"]),
    ("Robust slowing (after vs before the error)", pes["ASSISTments"]["cox_robust_pes"]["zE1"]),
]
fig, ax = plt.subplots(figsize=(6.6, 4.6))
y = np.arange(len(rows))[::-1]
labels = []
for yi, (lab, r) in zip(y, rows):
    if r is None:
        labels.append(lab)
        continue
    labels.append("   " + lab)
    hr, lo, hi = r["HR"], r["95ci"][0], r["95ci"][1]
    conf = "confirmatory" in lab
    col = BLUE if conf else (GREY if ("Robust" in lab or "rapid" in lab) else DARK)
    ax.errorbar(hr, yi, xerr=[[hr - lo], [hi - hr]], fmt="s" if conf else "o", color=col, capsize=2.5, ms=5 if conf else 4)
    ax.text(1.262, yi, f"{hr:.3f} ({lo:.3f}–{hi:.3f})", va="center", fontsize=7.5)
ax.axvline(1, color="#999999", lw=1, ls="--")
ax.set_yticks(y, labels, fontsize=8)
for t, (lab, r) in zip(ax.get_yticklabels(), rows):
    if r is None:
        t.set_fontweight("bold")
ax.set_xlim(0.95, 1.25)
ax.set_xlabel("Hazard ratio of mastery per SD of the slowing measure (95% CI); > 1 = faster mastery")
fig.savefig(os.path.join(fd, "fig_p1_forest.png"))
plt.close(fig)
print("figures written")
