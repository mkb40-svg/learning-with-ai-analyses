"""Shared figure style for the preprints."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLUE, GREY, DARK = "#1f5f99", "#8a8f98", "#222222"


def setup():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#555555",
        "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.6, "axes.axisbelow": True,
        "xtick.color": DARK, "ytick.color": DARK, "legend.frameon": False, "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })
    return plt
