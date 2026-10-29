"""Step 3. Fit and run the sky glow model.

1. World, 2.5 arc minutes: upward light per cell = mean VIIRS radiance x lit area (WorldPop 2023 lights).
2. Fit alpha, L and k (code/skyglow.py) to Globe at Night Sky Quality Meter readings taken under a clear sky after
   20:00 local time in 2019 to 2025 and darker than 18 mag/arcsec2, by least absolute error, with spatial
   cross-validation (5 folds of 10 degree blocks).
3. Run the fitted model for the world (2023) and for the UK at 30 arc seconds (2015, 2019 and 2023), adding glow from
   lights outside the UK and Ireland from the world grid.
Writes work/model.json, work/world_sky.npz (artificial brightness, micro cd/m2, float16), work/uk_sky_<year>.npz.
Run: python3 code/03_model.py
"""
import csv, json, os, sys
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import skyglow as S
W = os.path.join(ROOT, "work")
WC = 1 / 24; UC = 1 / 120
ROWS = (int((90 - 76) / WC), int((90 + 60) / WC))   # model rows 76N to 60S
GRID = [(a, L) for a in (2.0, 2.3, 2.6, 2.9) for L in (0, 50, 100)]


def world_emission():
    z = np.load(os.path.join(W, "world.npz"))
    lat = 90 - (np.arange(z["rad"].shape[0]) + .5) * WC
    a3 = S.cell_area_km2(lat, 1 / 1200)[:, None]          # one 3 arc second pixel
    return (z["rad"] * z["cnt"] * a3).astype(np.float64), z["pop"].astype(np.float64)


def gan_points(years=(2019, 2025), types=("GAN",)):
    pts = []
    for r in csv.DictReader(open(os.path.join(W, "gan_sqm.csv"))):
        y = int(r["year"])
        if years[0] <= y <= years[1] and r["type"] in types:
            pts.append((float(r["lat"]), float(r["lon"]), float(r["sqm"]), y))
    return np.array(pts)


def sample(G, lat, lon, lat0, lon0, cell):
    r = (lat0 - lat) / cell - .5; c = (lon - lon0) / cell - .5
    return map_coordinates(G, [r, c], order=1, mode="nearest")


FIT_MIN = 18.0   # fit only to readings darker than this: the 4.6 km world grid cannot resolve bright city-centre streets


def fit_k(s, m):
    """Scale k by least absolute error in magnitudes (robust to cloud, moon and meter outliers), readings >= FIT_MIN."""
    ok = (s > 0) & (m >= FIT_MIN)
    def loss(lk): return np.mean(np.abs(S.to_mag(10 ** lk * s[ok]) - m[ok]))
    r = minimize_scalar(loss, bounds=(-6, 12), method="bounded")
    return r.x, float(r.fun)


def stats(pred, obs):
    e = pred - obs
    return dict(rmse=float(np.sqrt(np.mean(e ** 2))), mae=float(np.mean(np.abs(e))), bias=float(np.mean(e)),
                r=float(np.corrcoef(pred, obs)[0, 1]), n=int(len(obs)))


if __name__ == "__main__":
    E, pop = world_emission()
    P = gan_points()
    lat, lon, m = P[:, 0], P[:, 1], P[:, 2]
    keep = (lat < 76) & (lat > -60); lat, lon, m = lat[keep], lon[keep], m[keep]
    blocks = (np.floor(lat / 10) * 37 + np.floor(lon / 10)).astype(int)
    rng = np.random.default_rng(1); ub = np.unique(blocks); fold_of = dict(zip(ub, rng.integers(0, 5, len(ub))))
    fold = np.array([fold_of[b] for b in blocks])
    res = []
    for a, L in GRID:
        Sg = S.convolve(E, 90, WC, a, L, rows=ROWS, wrap=True)
        s = sample(Sg, lat, lon, 90, -180, WC)
        lk, rm = fit_k(s, m)
        cv = np.zeros_like(m)
        for k in range(5):
            tr = fold != k; lk_k, _ = fit_k(s[tr], m[tr]); cv[~tr] = S.to_mag(10 ** lk_k * s[~tr])
        st = stats(cv, m); st18 = stats(cv[m >= FIT_MIN], m[m >= FIT_MIN])
        res.append(dict(alpha=a, L=L, log10k=lk, mae_fit=rm, cv=st, cv18=st18)); del Sg
        print(a, L, round(lk, 3), round(rm, 3), round(st18["mae"], 3), round(st["rmse"], 3), round(st["r"], 3), flush=True)
    best = min(res, key=lambda r: r["cv18"]["mae"])
    a, L, k = best["alpha"], best["L"], 10 ** best["log10k"]
    Sg = S.convolve(E, 90, WC, a, L, rows=ROWS, wrap=True)
    Bw = (k * Sg).astype(np.float32)
    np.savez_compressed(os.path.join(W, "world_sky.npz"), sky=S.f16_coarse(np.minimum(Bw, 60000)))
    s = sample(Sg, lat, lon, 90, -180, WC); pred = S.to_mag(k * s)
    np.save(os.path.join(W, "gan_fit.npy"), np.c_[lat, lon, m, pred])
    del Sg

    # older readings (2012 to 2018) against the same 2023 model: a check on drift, not a fit
    P2 = gan_points((2012, 2018)); k2 = (P2[:, 0] < 76) & (P2[:, 0] > -60); P2 = P2[k2]
    p2 = S.to_mag(k * sample(Bw / k, P2[:, 0], P2[:, 1], 90, -180, WC))
    old = stats(p2, P2[:, 2])

    # UK and Ireland at 30 arc seconds
    cid = np.load(os.path.join(W, "world_country.npz"))["cid"]; areas = json.load(open(os.path.join(W, "areas.json")))
    iso = {c["i"]: c["iso3"] for c in areas["countries"]}
    home = np.isin(cid, [i for i, c in iso.items() if c in ("GBR", "IRL", "IMN")])
    Ef = np.where(home, 0, E)
    rr = (int((90 - 66) / WC), int((90 - 44) / WC))
    Sf = S.convolve(Ef, 90, WC, a, L, rows=rr, wrap=True)
    z = np.load(os.path.join(W, "uk.npz"))
    UH, UW = z["cnt"].shape
    ulat = 61 - (np.arange(UH) + .5) * UC; ulon = -11 + (np.arange(UW) + .5) * UC
    LA, LO = np.meshgrid(ulat, ulon, indexing="ij")
    foreign = k * sample(Sf, LA.ravel(), LO.ravel(), 90, -180, WC).reshape(UH, UW)
    a3u = S.cell_area_km2(ulat, 1 / 1200)[:, None]
    uk = {}
    for y in (2015, 2019, 2023):
        Eu = (z[f"rad_{y}"] / np.maximum(z["cnt"], 1) * z["cnt"] * a3u).astype(np.float64)
        Su = S.convolve(Eu, 61, UC, a, L, band_rows=32, sub=3)
        Bu = (k * Su + foreign).astype(np.float32)
        np.savez_compressed(os.path.join(W, f"uk_sky_{y}.npz"), sky=S.f16_coarse(Bu, 2)); uk[y] = Bu
        print("uk", y, float(np.median(Bu)), flush=True)
    # UK points: fine model against the readings
    inuk = (P[:, 0] > 49.8) & (P[:, 0] < 61) & (P[:, 1] > -11) & (P[:, 1] < 2)
    Pu = P[inuk]
    pu = S.to_mag(sample(uk[2023], Pu[:, 0], Pu[:, 1], 61, -11, UC)) if len(Pu) else np.array([])
    puw = S.to_mag(sample(Bw, Pu[:, 0], Pu[:, 1], 90, -180, WC)) if len(Pu) else np.array([])
    by = {}
    for lo in np.arange(16, 22.5, .5):
        sel = (m >= lo) & (m < lo + .5)
        if sel.sum() >= 20: by[f"{lo:.1f}"] = dict(n=int(sel.sum()), median_err=float(np.median(pred[sel] - m[sel])))
    json.dump(dict(grid=res, best=best, fit_min=FIT_MIN, err_by_obs=by, k=k, alpha=a, L=L, d0=S.D0, r_max=S.R_MAX, natural=S.NATURAL,
                   older_readings=old, uk_points=dict(fine=stats(pu, Pu[:, 2]) if len(Pu) > 2 else None,
                                                      coarse=stats(puw, Pu[:, 2]) if len(Pu) > 2 else None)),
              open(os.path.join(W, "model.json"), "w"), indent=1)
    print("best", best)
