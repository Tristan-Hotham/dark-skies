"""Step 9. header.png: 1200 x 630 social card (title, the world sky glow map and the UK at 1 km).
Run: python3 code/09_header.py
"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import figlib as F
import matplotlib.pyplot as plt
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
Bw = np.load(os.path.join(ROOT, "work", "world_sky.npz"))["sky"].astype(np.float32)
U = np.load(os.path.join(ROOT, "work", "uk_sky_2023.npz"))["sky"].astype(np.float32)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=F.BG)
ax = fig.add_axes([0.035, 0.07, 0.62, 0.62]); ax.set_facecolor("#0E1020")
r0, r1 = int((90 - 72) * 24), int((90 + 56) * 24)
ax.imshow(F.sky_rgb(np.maximum(Bw[r0:r1], .5)), extent=[-180, 180, -56, 72], aspect="auto", interpolation="bilinear")
ax.set_xlim(-170, 180); ax.axis("off")
ax2 = fig.add_axes([0.675, 0.07, 0.29, 0.86]); ax2.set_facecolor("#0E1020")
ax2.imshow(F.sky_rgb(np.maximum(U, .5)), extent=[-11, 2, 49.8, 61], aspect=1 / np.cos(np.radians(55)), interpolation="nearest")
ax2.set_xlim(-8.3, 1.9); ax2.set_ylim(49.85, 60.9); ax2.axis("off")
fig.text(0.035, 0.94, "Darkest skies", fontproperties=F.DISP, fontsize=50, color=F.NIGHT, va="top")
fig.text(0.035, 0.80, f"Where you can still see the Milky Way. By my model {R['world']['pop_mw'] * 100:.0f}% of the world's\npeople, and {R['uk']['pop_mw'] * 100:.0f}% of the UK's, live under skies too bright for it.",
         fontsize=13.5, family=F.SER, color=F.MUT, va="top", linespacing=1.3)
fig.text(0.655, 0.035, "maps.tristanhotham.com", fontsize=10.5, family=F.MONO, color=F.MUT, ha="right")
fig.savefig(os.path.join(ROOT, "header.png"), facecolor=F.BG); plt.close(fig)
print("header written")
