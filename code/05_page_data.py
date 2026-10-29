"""Step 5. Files the interactive page reads.
  data/page/world_sky.png  : 5 arc minute world grid (75N to 60S, 4320 x 1620), red = coded sky brightness, green = land
  data/page/world_lit.png  : the same grid, coded VIIRS radiance (lights seen from space), 2023
  data/page/uk_sky.png     : 30 arc second UK and Ireland grid (1560 x 1344), red = sky 2023, green = sky 2015,
                             blue = UK area index (county or Northern Ireland district),
                             200 other land, 0 sea
  data/page/uk_lit.png     : UK grid, coded VIIRS radiance 2023
  data/page/search_uk.json : towns and villages of Great Britain (OS Open Names) and Northern Ireland (GeoNames)
  data/page/search_world.json : GeoNames places of 15,000 people or more
  data/page/borders.json   : simplified country outlines (Natural Earth 1:50m) and UK county outlines
Codes: sky v = 1 + round(254 * (log10(B) - log10(0.5)) / (log10(20000) - log10(0.5))), 0 when B < 0.5 micro cd/m2.
       light v = 1 + round(254 * log10(1 + r) / log10(1 + 400)), 0 when r < 0.05 nW/cm2/sr.
Run: python3 code/05_page_data.py
"""
import csv, io, json, os, sys, zipfile
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import skyglow as S
W = os.path.join(ROOT, "work"); P = os.path.join(ROOT, "data", "page"); os.makedirs(P, exist_ok=True)
SKY_LO, SKY_HI = 0.5, 20000.0
NE50 = "/home/claude/hist/_data3/ne/geojson/ne_50m_admin_0_countries.geojson"
UKC = "/home/claude/hist/how-roman-is-your-road/data/counties.geojson"
LTLA = "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson"


def code_sky(B):
    v = 1 + np.round(254 * (np.log10(np.maximum(B, 1e-9)) - np.log10(SKY_LO)) / (np.log10(SKY_HI) - np.log10(SKY_LO)))
    v = np.clip(v, 1, 255); v[B < SKY_LO] = 0
    return v.astype(np.uint8)


def code_lit(r):
    v = 1 + np.round(254 * np.log10(1 + np.maximum(r, 0)) / np.log10(401))
    v = np.clip(v, 1, 255); v[r < 0.05] = 0
    return v.astype(np.uint8)


def block_mean(a, f):
    h, w = a.shape; return a[:h - h % f, :w - w % f].reshape(h // f, f, w // f, f).mean(axis=(1, 3))


def simplify_geo(feats, tol, nd=3, name_key=None):
    from shapely.geometry import shape, mapping
    out = []
    for f in feats:
        g = shape(f["geometry"])
        if g.geom_type == "GeometryCollection":
            from shapely.ops import unary_union
            g = unary_union([x for x in g.geoms if x.geom_type in ("Polygon", "MultiPolygon")])
        g = g.simplify(tol, preserve_topology=True)
        if g.is_empty: continue
        def r(c):
            if isinstance(c[0], (int, float)): return [round(c[0], nd), round(c[1], nd)]
            return [r(x) for x in c]
        m = mapping(g); out.append({"type": "Feature", "properties": {"n": f["properties"].get(name_key) if name_key else None},
                                     "geometry": {"type": m["type"], "coordinates": r(m["coordinates"])}})
    return out


if __name__ == "__main__":
    Bw = np.load(os.path.join(W, "world_sky.npz"))["sky"].astype(np.float32)
    r0, r1 = int((90 - 75) * 24), int((90 + 60) * 24)
    Bc = block_mean(Bw[r0:r1].astype(np.float64), 2)
    cidw = np.load(os.path.join(W, "world_country.npz"))["cid"][r0:r1]
    landc = (cidw.reshape(cidw.shape[0] // 2, 2, cidw.shape[1] // 2, 2) > 0).any(axis=(1, 3))
    Image.fromarray(np.dstack([code_sky(Bc), (landc * 255).astype(np.uint8), np.zeros_like(code_sky(Bc))]), "RGB").save(os.path.join(P, "world_sky.png"), optimize=True)
    z = np.load(os.path.join(W, "world.npz"))
    lit = block_mean(z["rad"][r0:r1].astype(np.float64) * (z["cnt"][r0:r1] / 2500.0), 2)
    Image.fromarray(code_lit(lit), "L").save(os.path.join(P, "world_lit.png"), optimize=True)
    U23 = np.load(os.path.join(W, "uk_sky_2023.npz"))["sky"].astype(np.float32); U15 = np.load(os.path.join(W, "uk_sky_2015.npz"))["sky"].astype(np.float32)
    uid = np.load(os.path.join(W, "uk_area.npz"))["uid"].astype(np.uint8)
    cid = np.load(os.path.join(W, "world_country.npz"))["cid"]
    rr = ((90 - (61 - (np.arange(uid.shape[0]) + .5) / 120)) * 24).astype(int); cc = ((-11 + (np.arange(uid.shape[1]) + .5) / 120 + 180) * 24).astype(int)
    gbr = [i + 1 for i, f in enumerate(json.load(open(os.path.join(W, "areas.json")))["countries"]) if f["iso3"] == "GBR"]
    cu = cid[rr][:, cc]
    uid[(uid == 0) & (cu > 0) & ~np.isin(cu, gbr)] = 200      # other countries' land (Ireland, France, Isle of Man): 200
    rgb = np.dstack([code_sky(U23), code_sky(U15), uid])
    Image.fromarray(rgb, "RGB").save(os.path.join(P, "uk_sky.png"), optimize=True)
    zu = np.load(os.path.join(W, "uk.npz"))
    ur = zu["rad_2023"] / np.maximum(zu["cnt"], 1) * (zu["cnt"] / 100.0)
    Image.fromarray(code_lit(ur), "L").save(os.path.join(P, "uk_lit.png"), optimize=True)

    # search lists
    uk = []
    with open("/home/claude/hist/osnames_gb.tsv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if r["local_type"] in ("City", "Town", "Village", "Suburban Area"):
                k = {"City": 3, "Town": 2, "Village": 1, "Suburban Area": 0}[r["local_type"]]
                nm = f'{r["name2"]} ({r["name1"]})' if r["lang1"] in ("cym", "gla") and r["name2"] else r["name1"]
                uk.append([nm, round(float(r["lat"]), 4), round(float(r["lon"]), 4), k, r["county"] or r["district"] or r["region"]])
    zf = zipfile.ZipFile("/home/claude/hist/_data13/cities15000.zip"); txt = io.TextIOWrapper(zf.open("cities15000.txt"), encoding="utf-8")
    world = []
    for ln in txt:
        f = ln.rstrip("\n").split("\t")
        if f[7] == "PPLX": continue
        p = int(f[14] or 0)
        f[1] = f[1].replace("\u2013", "-").replace("\u2014", "-")
        world.append([f[1], round(float(f[4]), 3), round(float(f[5]), 3), p, f[8]])
        if f[8] == "GB" and f[10] == "NIR":
            uk.append([f[1], round(float(f[4]), 4), round(float(f[5]), 4), 3 if p >= 100000 else 2, "Northern Ireland"])
    world.sort(key=lambda x: -x[3])
    json.dump(uk, open(os.path.join(P, "search_uk.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    json.dump(world, open(os.path.join(P, "search_world.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    # borders
    ne = json.load(open(NE50))["features"]
    cb = simplify_geo(ne, 0.05, 2, "NAME")
    ukf = json.load(open(UKC))["features"]; ni = [f for f in json.load(open(LTLA))["features"] if f["properties"]["areacd"].startswith("N")]
    for f in ni: f["properties"]["county"] = f["properties"]["areanm"]
    ub = simplify_geo(ukf + ni, 0.004, 3, "county")
    json.dump({"countries": cb, "uk": ub}, open(os.path.join(P, "borders.json"), "w"), separators=(",", ":"))
    for f in sorted(os.listdir(P)): print(f, os.path.getsize(os.path.join(P, f)))
