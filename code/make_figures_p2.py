"""Final figures for Preprint 2, drawn from results/p2_robust.json (no recomputation).

Usage: python -I make_figures_p2.py <results_dir> <figure_dir>
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import setup, BLUE, GREY, DARK  # noqa: E402

rd, fd = sys.argv[1:3]
plt = setup()
r = json.load(open(os.path.join(rd, "p2_robust.json"), encoding="utf-8"))
pct = plt.FuncFormatter(lambda v, _: f"{100 * v:.0f}%")

# Figure 1: ASSISTments
fa = r["A_figure_data"]
labels = ["Correct on first attempt", "Error, no hint", "Hints after an attempt,\nanswer not shown",
          "Hint before any attempt,\nanswer not shown", "Answer shown"]
keys = [l.replace("\n", " ") for l in labels]
m = np.array([fa[k]["mean"] for k in keys]); ci = np.array([fa[k]["ci95"] for k in keys]); n = [fa[k]["learners"] for k in keys]
fig, ax = plt.subplots(figsize=(6.3, 2.7))
y = np.arange(len(keys))[::-1]
ax.errorbar(m, y, xerr=ci, fmt="o", color=BLUE, capsize=3, ms=6)
for yi, mi, ci_, ni in zip(y, m, ci, n):
    ax.text(mi + ci_ + 0.015, yi, f"{100 * mi:.0f}%  (pupils: {ni:,})", va="center", fontsize=7.5, color=DARK)
ax.set_yticks(y, labels)
ax.set_xlim(0.3, 0.9)
ax.xaxis.set_major_formatter(pct)
ax.set_xlabel("Next problem of the same skill answered correctly (mean over pupils, 95% CI)")
fig.savefig(os.path.join(fd, "fig_p2_assistments.png"))
plt.close(fig)

# Figure 2: EdNet-KT3
dec = r["B_figure_data"]["deciles"]; nv = r["B_figure_data"]["not_viewed"]
sec = [d["sec"] for d in dec]; p = [d["p"] for d in dec]; e = [d["ci"] for d in dec]
fig, ax = plt.subplots(figsize=(6.3, 2.9))
ax.errorbar(sec, p, yerr=e, fmt="o-", color=BLUE, capsize=2, ms=4, lw=1.2, label="Explanation opened: deciles of time spent")
ax.axhline(nv["p"], color=GREY, ls="--", lw=1.2, label=f"Explanation not opened (n = {nv['n']:,} errors)")
ax.set_xscale("log")
ax.set_xticks([2, 5, 10, 20, 50, 100, 200], ["2", "5", "10", "20", "50", "100", "200"])
ax.set_ylim(0.58, 0.66)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{100 * v:.1f}%"))
ax.set_xlabel("Median seconds on the explanation in each decile (log scale)")
ax.set_ylabel("Next answer on the same\ntopic correct")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=1, fontsize=8)
fig.savefig(os.path.join(fd, "fig_p2_ednet.png"))
plt.close(fig)
print("figures written")
