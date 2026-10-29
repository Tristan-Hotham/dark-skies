"""r/dataisbeautiful collage: reddit/dark_skies.png (2400 x 3000), pale moonlit paper with night panels.
Hero: the UK at 1 km in the night palette, with four big numbers. Below: the world map, the distance from UK cities
to a Milky Way sky, and people against land in the four nations. Every number comes from ../data/results.json.
Fonts: FONT_DIR (Fraunces, Source Serif 4, IBM Plex Mono).
Also writes reddit/post.md (title, body and source comment) from the same results.
Run: python3 reddit/collage.py
"""
import json, os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "code"))
import figlib as F
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
BG, INK, MUT, NIGHT = "#EEECF3", "#191A2B", "#5C5C70", "#0E1020"
ROSE, AMBER, NAVY = "#C8466F", "#D9861C", "#1B2147"
Bw = np.load(os.path.join(ROOT, "work", "world_sky.npz"))["sky"].astype(np.float32)
U = np.load(os.path.join(ROOT, "work", "uk_sky_2023.npz"))["sky"].astype(np.float32)
BORD = json.load(open(os.path.join(ROOT, "data", "page", "borders.json")))
pct = lambda v: f"{round(v * 100)}%"

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)


def panel(x, y, w, h, fc=NIGHT):
    fig.patches.append(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.008", transform=fig.transFigure, fc=fc, ec="none", zorder=0))


# title and dek
fig.text(0.04, 0.976, "Where can you still", fontproperties=F.DISP, fontsize=46, color=INK, va="top")
fig.text(0.04, 0.931, "see the Milky Way?", fontproperties=F.DISP, fontsize=46, color=ROSE, va="top")
fig.text(0.04, 0.879, "A model of the glow our lights throw into the night sky, built from satellite images of the Earth at night\n"
         f"(VIIRS, 2023) and checked against {R['model']['n_fit']:,} readings from volunteers' sky meters. Rose and amber: too bright to see it.",
         family=F.SER, fontsize=14.5, color=INK, va="top", linespacing=1.4)

# hero UK map
ax = fig.add_axes([0.04, 0.293, 0.431, 0.53]); ax.set_facecolor(NIGHT)
asp = 1 / np.cos(np.radians(54.5))
ax.imshow(F.sky_rgb(np.maximum(U, .5)), extent=[-11, 2, 49.8, 61], interpolation="nearest", aspect=asp)
for f in BORD["uk"]:
    g = f["geometry"]; polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
    for poly in polys:
        a = np.array(poly[0]); ax.plot(a[:, 0], a[:, 1], color="white", lw=.25, alpha=.25)
ax.set_xlim(-8.3, 1.9); ax.set_ylim(49.9, 59.0); ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
lab = dict(color="white", fontsize=10.5, family=F.MONO)
for name, (la, lo), (tla, tlo), ha in [("London", (51.507, -0.128), (51.05, 0.85), "left"), ("Manchester", (53.48, -2.24), (53.85, -0.75), "left"),
                                       ("Glasgow", (55.86, -4.25), (56.45, -5.7), "right"), ("Galloway Forest", (55.12, -4.42), (54.45, -3.3), "left"),
                                       ("Northumberland", (55.3, -2.3), (55.75, -0.9), "left"), ("Cairngorms", (57.08, -3.67), (56.7, -1.8), "left"),
                                       ("Outer Hebrides", (57.9, -6.9), (58.75, -7.9), "left"), ("Dartmoor", (50.57, -3.92), (50.25, -5.6), "right")]:
    ax.annotate(name, (lo, la), (tlo, tla), ha=ha, va="center", arrowprops=dict(arrowstyle="-", color="white", lw=.7, alpha=.85), **lab)
ax.text(-8.15, 49.98, "Britain and Ireland at about 1 km", color="white", alpha=.8, fontsize=10, family=F.MONO)

# big numbers
nums = [(pct(R["world"]["pop_mw"]), ROSE, f"of the world's people live where the\nglow hides the Milky Way. The 2016\nWorld Atlas said {pct(R['falchi']['pop_mw'])}, with older data"),
        (pct(R["uk"]["pop_mw"]), ROSE, f"of people in the UK, about\n{R['uk']['people_mw_m']:.0f} million. England {pct(R['uk']['nations']['England']['pop_mw'])},\nNorthern Ireland {pct(R['uk']['nations']['Northern Ireland']['pop_mw'])}"),
        (pct(R["uk"]["land_mw_visible"]), NAVY, "of UK land still has a sky where\nit shows: people are packed into\nthe bright places"),
        (f"{R['uk_cities']['London']['mw_km']} km", AMBER, "from central London to the nearest\nMilky Way sky, near Toys Hill\nin Kent")]
for i, (big, col, small) in enumerate(nums):
    y = 0.822 - i * 0.108
    fig.text(0.51, y, big, fontproperties=F.DISP, fontsize=40, color=col, va="top")
    fig.text(0.512, y - 0.047, small, family=F.SER, fontsize=12.5, color=INK, va="top", linespacing=1.3)
# mini chart: UK cities, km to a Milky Way sky
names = ["London", "Birmingham", "Manchester", "Leeds", "Glasgow", "Cardiff", "Edinburgh"]
ac = fig.add_axes([0.64, 0.297, 0.32, 0.066]); ac.set_facecolor(BG)
vals = [R["uk_cities"][n]["mw_km"] for n in names]
ac.barh(range(len(names))[::-1], vals, color=NAVY, height=.62)
for i, (n, v) in enumerate(zip(names, vals)):
    ac.text(-1, len(names) - 1 - i, n, ha="right", va="center", family=F.MONO, fontsize=10, color=INK)
    ac.text(v + .8, len(names) - 1 - i, f"{v}", va="center", family=F.MONO, fontsize=10, color=INK)
ac.set_xlim(0, max(vals) * 1.15); ac.axis("off")
fig.text(0.51, 0.372, "KM FROM THE CITY CENTRE TO A MILKY WAY SKY", family=F.MONO, fontsize=10, color=MUT)

# world strip
aw = fig.add_axes([0.04, 0.08, 0.92, 0.205]); aw.set_facecolor(NIGHT)
r0, r1 = int((90 - 72) * 24), int((90 + 56) * 24)
aw.imshow(F.sky_rgb(np.maximum(Bw[r0:r1], .5)), extent=[-180, 180, -56, 72], aspect="auto", interpolation="bilinear")
aw.set_xlim(-168, 180); aw.set_ylim(-38, 62); aw.set_xticks([]); aw.set_yticks([])
for sp in aw.spines.values(): sp.set_visible(False)
aw.text(-165, -34, f"The world, 2023. Most people cannot see the Milky Way in {R['countries_mw_over_half']} of {R['countries_n']} countries of a million or more",
        color="white", alpha=.85, fontsize=10, family=F.MONO)

# footer
fig.text(0.04, 0.069, "Data: night lights from the Earth Observation Group VIIRS VNL v2 via WorldPop (CC BY 4.0); population: WorldPop 2023 (CC BY 4.0);\n"
         "sky meter readings: Globe at Night, NOIRLab (CC BY 4.0); thresholds: Falchi et al. 2016, Science Advances. Own sky glow model,\n"
         f"tuned to sky meter readings (typical error {R['model']['cv18_mae']:.2f} mag/arcsec²); glow above about 4x the natural sky hides the Milky Way.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.   maps.tristanhotham.com/dark-skies",
         family=F.MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.45)
fig.savefig(os.path.join(HERE, "dark_skies.png"), facecolor=BG)
print("collage written")

p = lambda v: f"{round(v * 100)}%"
post = f"""# Reddit post

## Title

[OC] Where can you still see the Milky Way? A sky glow model of the world and the UK at 1 km from 2023 satellite night lights: {p(R['world']['pop_mw'])} of people worldwide and {p(R['uk']['pop_mw'])} in the UK live under skies too bright for it

## Body (optional)

I spread the light that the VIIRS satellite sees at night (2023) across the sky around each source with a simple distance rule, and tuned that rule against {R['model']['n_fit']:,} sky meter readings from Globe at Night volunteers. By this model {p(R['world']['pop_mw'])} of the world's people cannot see the Milky Way from home (the 2016 World Atlas said {p(R['falchi']['pop_mw'])}, with 2014 lights, and ranks countries almost the same way). In the UK it is {p(R['uk']['pop_mw'])} of people but only {p(R['uk']['land_mw'])} of the land; the darkest areas are the Western Isles and the Highlands, and from central London the nearest Milky Way sky is {R['uk_cities']['London']['mw_km']} km away. Caveat: it is a model, typically within {R['model']['cv18_mae']:.1f} magnitudes of the meter readings outside city centres. Find your own sky: https://maps.tristanhotham.com/dark-skies/

## Source comment

Source: night lights from the Earth Observation Group's annual VIIRS composites (VNL v2), as resampled per country by WorldPop (CC BY 4.0); population: WorldPop 2023, R2025A (CC BY 4.0); Sky Quality Meter readings: Globe at Night, NOIRLab (CC BY 4.0); thresholds and comparison figures: Falchi et al. (2016), The new world atlas of artificial night sky brightness, Science Advances; Dark Sky Places: English Wikipedia (CC BY-SA 4.0); places: OS Open Names (OGL v3) and GeoNames (CC BY 4.0); boundaries: Natural Earth and ONS.

Tools: Python (numpy, scipy, matplotlib, Pillow, shapely) and a web browser to read the WorldPop GeoTIFFs; Leaflet for the interactive map.

Interactive map: https://maps.tristanhotham.com/dark-skies/
Blog post: https://blog.tristanhotham.com/2026/10/29/dark-skies/
Paper and data: https://doi.org/10.5281/zenodo.23757708
"""
for b in ("\u2014", "\u2013", "--"): assert b not in post
open(os.path.join(HERE, "post.md"), "w").write(post)
print("post written")
