"""Shared drawing helpers for the static figures, header and collage: fonts, the night palette used on the page,
and loaders for the model grids."""
import json, os
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
W = os.path.join(ROOT, "work")
FD = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts")
if os.path.exists(os.path.join(FD, "FrauncesVar.ttf")):
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
        fm.fontManager.addfont(os.path.join(FD, f))
    DISP = fm.FontProperties(fname=os.path.join(FD, "FrauncesVar.ttf"), weight=900)
    SER, MONO = "Source Serif 4", "IBM Plex Mono"
else:
    DISP = fm.FontProperties(family="DejaVu Serif", weight="bold"); SER, MONO = "DejaVu Serif", "DejaVu Sans Mono"
BG, FG, MUT, RULE = "#F5F3EE", "#191A2B", "#5F6072", "#DBD6CC"
NIGHT, VIOLET, ROSE, AMBER, STAR = "#1B2147", "#5B3F8C", "#C8466F", "#D9861C", "#F3D27A"
TH = [1.74, 13.9, 87.0, 688.0, 3000.0]
STOPS = [(0.5, (14, 18, 48)), (1.74, (20, 27, 74)), (13.9, (42, 58, 140)), (87, (98, 70, 168)), (300, (176, 72, 150)), (688, (222, 86, 112)),
         (3000, (242, 156, 72)), (8000, (250, 214, 120)), (20000, (255, 249, 226))]


def sky_rgb(B):
    """RGB (0..1) for artificial brightness B (micro cd/m2), same stops as the page."""
    B = np.asarray(B, float); lb = np.log10(np.clip(B, STOPS[0][0], STOPS[-1][0]))
    xs = np.log10([s[0] for s in STOPS]); cs = np.array([s[1] for s in STOPS]) / 255
    return np.stack([np.interp(lb, xs, cs[:, k]) for k in range(3)], axis=-1)


def sky_cmap(n=256):
    b = 10 ** np.linspace(np.log10(0.5), np.log10(20000), n)
    return ListedColormap(sky_rgb(b))


def load(name):
    return json.load(open(os.path.join(ROOT, "data", name)))


def mag(b):
    return 22.0 - 2.5 * np.log10((np.asarray(b) + 174.0) / 174.0)


def style(ax, grid=True):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=12)
    for t in ax.get_xticklabels() + ax.get_yticklabels(): t.set_fontfamily(MONO)
    if grid: ax.grid(axis="x", color=RULE, lw=.8); ax.set_axisbelow(True)
