"""Step 8. Static figures for the blog (release/blog/b_*.png, 1520 px wide) and the paper (release/paper/fig_*.png).
Drawn with matplotlib from work/ grids and data/results.json; maps are plate carree from the model grids.
Run: python3 code/08_figures.py
"""
import json, os, shutil, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import figlib as F
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path

R = json.load(open(os.path.join(ROOT, "data", "results.json")))
PD = json.load(open(os.path.join(ROOT, "work", "page_data.json")))
B = os.path.join(ROOT, "release", "blog"); P = os.path.join(ROOT, "release", "paper")
os.makedirs(B, exist_ok=True); os.makedirs(P, exist_ok=True)
DPI = 160; WIDE = 1520 / DPI
BORD = json.load(open(os.path.join(ROOT, "data", "page", "borders.json")))


def save(fig, name):
    fig.savefig(os.path.join(B, "b_" + name + ".png"), dpi=DPI, facecolor=F.BG)
    shutil.copy(os.path.join(B, "b_" + name + ".png"), os.path.join(P, "fig_" + name + ".png"))
    plt.close(fig); print(name)


def outline(ax, feats, lw=.3, col="#FFFFFF", alpha=.35, xlim=None):
    for f in feats:
        g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for poly in polys:
            for ring in poly:
                a = np.array(ring)
                ax.plot(a[:, 0], a[:, 1], color=col, lw=lw, alpha=alpha, solid_capstyle="round")


def world_map():
    Bw = np.load(os.path.join(ROOT, "work", "world_sky.npz"))["sky"].astype(np.float32)
    r0, r1 = int((90 - 75) * 24), int((90 + 58) * 24)
    img = F.sky_rgb(np.maximum(Bw[r0:r1], .5))
    fig = plt.figure(figsize=(WIDE, WIDE * 0.5), facecolor=F.BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#0E1020")
    ax.imshow(img, extent=[-180, 180, -58, 75], interpolation="bilinear", aspect="auto")
    outline(ax, BORD["countries"], lw=.25, alpha=.28)
    ax.set_xlim(-170, 180); ax.set_ylim(-56, 75); ax.axis("off")
    save(fig, "world_map")


def uk_map():
    U = np.load(os.path.join(ROOT, "work", "uk_sky_2023.npz"))["sky"].astype(np.float32)
    img = F.sky_rgb(np.maximum(U, .5))
    x0, x1, y0, y1 = -8.4, 1.9, 49.9, 59.4
    asp = 1 / np.cos(np.radians(54.5)); ratio = (y1 - y0) * asp / (x1 - x0)
    fig = plt.figure(figsize=(WIDE, WIDE * ratio), facecolor="#0E1020")
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_facecolor("#0E1020")
    ax.imshow(img, extent=[-11, 2, 49.8, 61], interpolation="nearest", aspect=asp)
    outline(ax, BORD["uk"], lw=.3, alpha=.3)
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.axis("off")
    for name, (la, lo), (tla, tlo), ha in [("London", (51.507, -0.128), (51.0, 0.9), "left"), ("Manchester", (53.48, -2.24), (53.75, -0.9), "left"),
                                           ("Glasgow", (55.86, -4.25), (56.35, -5.6), "right"), ("Galloway Forest", (55.12, -4.42), (54.75, -5.9), "right"),
                                           ("Kielder", (55.23, -2.58), (55.55, -1.1), "left"), ("Cardiff", (51.48, -3.18), (52.05, -5.0), "right"),
                                           ("Belfast", (54.6, -5.93), (55.35, -7.0), "right"), ("Cairngorms", (57.08, -3.67), (56.7, -1.7), "left"),
                                           ("Exmoor", (51.1, -3.6), (50.55, -5.3), "right"), ("Outer Hebrides", (57.9, -6.9), (58.75, -7.4), "left")]:
        ax.annotate(name, (lo, la), (tlo, tla), color="white", fontsize=13, family=F.MONO, ha=ha, va="center",
                    arrowprops=dict(arrowstyle="-", color="white", lw=.8, alpha=.85))
    cax = fig.add_axes([0.05, 0.035, 0.36, 0.016]); b = 10 ** np.linspace(np.log10(.5), np.log10(20000), 400)
    cax.imshow(F.sky_rgb(b)[None, :, :], aspect="auto", extent=[np.log10(.5), np.log10(20000), 0, 1]); cax.set_yticks([])
    cax.set_xticks(np.log10(F.TH)); cax.set_xticklabels(["1%", "8%", "50%", "4x", "17x"], color="white", fontsize=11.5, family=F.MONO)
    cax.tick_params(colors="white", length=4)
    for sp in cax.spines.values(): sp.set_visible(False)
    fig.text(0.05, 0.062, "Artificial glow, share of the natural night sky", color="white", fontsize=12.5, family=F.MONO)
    fig.savefig(os.path.join(B, "b_uk_map.png"), dpi=DPI, facecolor="#0E1020")
    shutil.copy(os.path.join(B, "b_uk_map.png"), os.path.join(P, "fig_uk_map.png")); plt.close(fig); print("uk_map")


def countries():
    rows = sorted([c for c in PD["countries"] if c[2] >= 30], key=lambda c: c[3])
    fig, ax = plt.subplots(figsize=(WIDE, 0.29 * len(rows) + 1.2), facecolor=F.BG); ax.set_facecolor(F.BG)
    y = np.arange(len(rows))
    ax.barh(y, [c[3] * 100 for c in rows], color=F.ROSE, height=.66, label="My model, 2023")
    fx = [(i, c[4] * 100) for i, c in enumerate(rows) if c[4] is not None]
    ax.scatter([v for _, v in fx], [i for i, _ in fx], marker="|", s=220, color=F.FG, lw=2.6, label="Falchi et al. 2016", zorder=3)
    ax.set_yticks(y); ax.set_yticklabels([c[1] for c in rows], fontsize=12, family=F.SER)
    ax.set_xlim(0, 100); ax.set_xlabel("People under a sky that hides the Milky Way, %", fontsize=13, family=F.MONO, color=F.FG)
    F.style(ax); ax.legend(frameon=False, fontsize=12, loc="lower right", prop={"family": F.MONO})
    fig.tight_layout(); save(fig, "countries")


def cities():
    rows = [c for c in PD["cities"][:25]][::-1]
    uk = [c for c in PD["ukcities"] if c[1] == "GB" and c[3] is not None][:12][::-1]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(WIDE, 8.2), facecolor=F.BG, gridspec_kw=dict(width_ratios=[1.15, 1], wspace=.55))
    for ax, rr, tt in [(a1, rows, "World's biggest cities"), (a2, uk, "UK cities")]:
        ax.set_facecolor(F.BG)
        ax.barh(range(len(rr)), [c[3] for c in rr], color=F.NIGHT, height=.66)
        ax.set_yticks(range(len(rr))); ax.set_yticklabels([c[0] for c in rr], fontsize=12, family=F.SER)
        for i, c in enumerate(rr): ax.text(c[3] + max(x[3] for x in rr) * .02, i, f"{c[3]:,}", va="center", fontsize=11, family=F.MONO, color=F.FG)
        ax.set_xlabel("km to the nearest Milky Way sky", fontsize=12.5, family=F.MONO, color=F.FG); F.style(ax)
        ax.set_title(tt, loc="left", fontsize=14, family=F.MONO, color=F.MUT)
        ax.set_xlim(0, max(x[3] for x in rr) * 1.18)
    fig.subplots_adjust(left=.17, right=.97, top=.94, bottom=.08); save(fig, "cities")


def fit():
    f = np.load(os.path.join(ROOT, "work", "gan_fit.npy")); m = R["model"]
    fig = plt.figure(figsize=(WIDE, WIDE * .52), facecolor=F.BG)
    ax = fig.add_axes([0.07, 0.13, 0.4, 0.8]); ax.set_facecolor(F.BG)
    ax.hexbin(f[:, 2], f[:, 3], gridsize=45, extent=(15.5, 22.2, 15.5, 22.2), mincnt=1, cmap="Purples", bins="log", linewidths=0)
    ax.plot([15.5, 22.2], [15.5, 22.2], color=F.FG, lw=1, ls="--")
    ax.set_xlim(15.5, 22.2); ax.set_ylim(15.5, 22.2)
    ax.set_xlabel("Measured, mag/arcsec²", fontsize=12.5, family=F.MONO); ax.set_ylabel("Model, mag/arcsec²", fontsize=12.5, family=F.MONO)
    F.style(ax, grid=False)
    ax.text(15.7, 21.95, f"{m['n_fit']:,} Globe at Night readings\n2019 to 2025, clear skies", va="top", fontsize=12, family=F.MONO, color=F.FG)
    a2 = fig.add_axes([0.58, 0.13, 0.39, 0.8]); a2.set_facecolor(F.BG)
    E = m["err_by_obs"]; xs = [float(k) + .25 for k in E]; ys = [E[k]["err"] for k in E]
    a2.bar(xs, ys, width=.42, color=[F.VIOLET if float(k) >= m["fit_min"] else "#B9B4C6" for k in E])
    a2.axhline(0, color=F.FG, lw=.8); a2.axvline(m["fit_min"], color=F.MUT, ls=":", lw=1)
    a2.set_xlabel("Measured, mag/arcsec² (bins)", fontsize=12.5, family=F.MONO)
    a2.set_ylabel("Median model error, mag", fontsize=12.5, family=F.MONO); F.style(a2, grid=False); a2.grid(axis="y", color=F.RULE)
    a2.text(m["fit_min"] + .1, max(ys) * .92, f"fitted to readings\ndarker than {m['fit_min']:.0f}\ncross-validated typical\nerror {m['cv18_mae']:.2f} mag", fontsize=11.5, family=F.MONO, va="top")
    save(fig, "fit")


def change():
    C = PD["change"]; yrs = C["years"]
    fig = plt.figure(figsize=(WIDE, 7.2), facecolor=F.BG)
    a1 = fig.add_axes([0.08, 0.12, 0.42, 0.82]); a1.set_facecolor(F.BG)
    for k, n, c in [("gbr", "Great Britain", F.NIGHT), ("irl", "Ireland", F.AMBER)]:
        v = np.array(C[k], float); v = v / v[0] * 100
        a1.plot(yrs, v, color=c, lw=2.6, marker="o", ms=5); a1.text(yrs[-1] + .2, v[-1], n, va="center", fontsize=12.5, family=F.MONO, color=c)
    a1.axhline(100, color=F.MUT, lw=.8); a1.set_xlim(2014.6, 2025.9); a1.set_xticks(yrs[::2]); F.style(a1); a1.grid(axis="y", color=F.RULE)
    a1.set_ylabel("Lights seen from space, 2015 = 100", fontsize=12.5, family=F.MONO)
    U23 = np.load(os.path.join(ROOT, "work", "uk_sky_2023.npz"))["sky"].astype(np.float32); U15 = np.load(os.path.join(ROOT, "work", "uk_sky_2015.npz"))["sky"].astype(np.float32)
    uid = np.load(os.path.join(ROOT, "work", "uk_area.npz"))["uid"]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log2(U23 / np.maximum(U15, 1e-6))
    r[uid == 0] = np.nan
    a2 = fig.add_axes([0.55, 0.13, 0.43, 0.84]); a2.set_facecolor(F.BG)
    im = a2.imshow(r, extent=[-11, 2, 49.8, 61], cmap="RdBu_r", vmin=-.6, vmax=.6, aspect=1 / np.cos(np.radians(55)), interpolation="nearest")
    a2.set_xlim(-8.4, 1.9); a2.set_ylim(49.85, 60.95); a2.axis("off")
    cax = fig.add_axes([0.6, 0.085, 0.33, 0.022])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", ticks=[-.585, 0, .585])
    cb.ax.set_xticklabels(["−33%", "no change", "+50%"], fontsize=11.5, family=F.MONO)
    fig.text(0.765, 0.008, "Modelled sky glow, 2023 lights against 2015", ha="center", fontsize=11.5, family=F.MONO, color=F.MUT)
    save(fig, "change")


def counties():
    A = [a for a in PD["areas"]]
    top = A[:10]; bot = A[-10:]
    rows = top + [None] + bot
    fig, ax = plt.subplots(figsize=(WIDE, 7.6), facecolor=F.BG); ax.set_facecolor(F.BG)
    ys = []; labs = []
    for i, a in enumerate(rows[::-1]):
        if a is None: continue
        m = a[3]; b = 174 * (10 ** (-0.4 * (m - 22)) - 1)
        ax.barh(i, m - 16, left=16, color=tuple(F.sky_rgb(max(b, .6))), height=.7, edgecolor=F.FG, lw=.3)
        ax.text(m + .05, i, f"{m:.2f}", va="center", fontsize=11, family=F.MONO)
        ys.append(i); labs.append(f"{a[0]} ({a[1]})" if a[1] != "England" else a[0])
    ax.set_yticks(ys); ax.set_yticklabels(labs, fontsize=12, family=F.SER); ax.set_xlim(16, 22.4)
    ax.set_xlabel("Median sky over the land, mag/arcsec² (higher = darker)", fontsize=12.5, family=F.MONO); F.style(ax)
    fig.tight_layout(); save(fig, "counties")


if __name__ == "__main__":
    import sys as _s
    only = _s.argv[1:]
    if only:
        for f in only: globals()[f]()
        raise SystemExit
    world_map(); uk_map(); countries(); cities(); fit(); change(); counties()
