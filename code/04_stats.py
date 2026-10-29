"""Step 4. Statistics from the modelled skies: world, countries, cities, UK nations, counties, council areas, towns,
Dark Sky Places, and change in the UK's lights from 2015 to 2023.
Thresholds (artificial zenith brightness, micro cd/m2) follow Falchi et al. (2016), so the results can be set beside
their Table 2: 1.74 (1% of natural, "pristine"), 13.9 ("light polluted"), 87 (half the natural sky), 688 (Milky Way
hidden) and 3000 (eyes cannot fully dark-adapt).
Writes work/stats.json and data CSVs (countries.csv, cities.csv, uk_areas.csv, uk_councils.csv, uk_towns.csv,
dark_sky_places.csv with modelled brightness).
Run: python3 code/04_stats.py
"""
import csv, io, json, os, sys, zipfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
import skyglow as S
W = os.path.join(ROOT, "work"); D = os.path.join(ROOT, "data")
WC = 1 / 24; UC = 1 / 120
TH = S.THRESH
TK = ["pristine", "polluted", "nat_lost", "milky_way", "no_dark_adapt"]
GEON = "/home/claude/hist/_data13/cities15000.zip"
OSN = "/home/claude/hist/osnames_gb.tsv"
R = lambda x, n=4: None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), n)


def shares(B, wgt):
    t = float(wgt.sum())
    if t <= 0: return None
    o = {"total": t, "le_pristine": float(wgt[B <= TH["pristine"]].sum() / t)}
    for k in TK: o[k] = float(wgt[B > TH[k]].sum() / t)
    return o


def wmedian(v, w):
    o = np.argsort(v); c = np.cumsum(w[o]); return float(v[o][np.searchsorted(c, c[-1] / 2)])


def hav(lat1, lon1, lat2, lon2):
    p = np.radians; a = np.sin(p(lat2 - lat1) / 2) ** 2 + np.cos(p(lat1)) * np.cos(p(lat2)) * np.sin(p(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0088 * np.arcsin(np.sqrt(a))


def nearest_below(B, lat0, lon0, cell, lat, lon, thr, radius_km=600, mask=None):
    """Distance (km) and position of the nearest cell with B below thr (and on land if mask given)."""
    H, Wd = B.shape
    r = int((lat0 - lat) / cell); c = int((lon - lon0) / cell)
    dr = int(radius_km / 111.2 / cell) + 1; dc = int(radius_km / (111.2 * max(.2, np.cos(np.radians(lat)))) / cell) + 1
    r0, r1, c0, c1 = max(0, r - dr), min(H, r + dr + 1), max(0, c - dc), min(Wd, c + dc + 1)
    sub = B[r0:r1, c0:c1]; ok = sub < thr
    if mask is not None: ok &= mask[r0:r1, c0:c1]
    ii, jj = np.nonzero(ok)
    if not len(ii): return None
    la = lat0 - (ii + r0 + .5) * cell; lo = lon0 + (jj + c0 + .5) * cell
    d = hav(lat, lon, la, lo); k = int(np.argmin(d))
    return float(d[k]), float(la[k]), float(lo[k])


def cell(B, lat0, lon0, cell, lat, lon):
    r = int((lat0 - lat) / cell); c = int((lon - lon0) / cell)
    if 0 <= r < B.shape[0] and 0 <= c < B.shape[1]: return float(B[r, c])
    return None


if __name__ == "__main__":
    out = {}
    areas = json.load(open(os.path.join(W, "areas.json")))
    z = np.load(os.path.join(W, "world.npz")); pop = z["pop"]; cnt = z["cnt"]; rad = z["rad"]
    Bw = np.load(os.path.join(W, "world_sky.npz"))["sky"].astype(np.float32); cid = np.load(os.path.join(W, "world_country.npz"))["cid"]
    H, Wd = Bw.shape
    lat = 90 - (np.arange(H) + .5) * WC
    area = np.broadcast_to(S.cell_area_km2(lat, WC)[:, None], Bw.shape)
    land = cid > 0
    band = np.zeros_like(land); band[int((90 - 75) / WC):int((90 + 60) / WC)] = True  # Falchi's land window 75N to 60S
    out["world"] = dict(pop=shares(Bw, pop), land=shares(Bw[land & band], area[land & band]),
                        pop_total=float(pop.sum()), land_km2=float(area[land & band].sum()))
    # population-weighted sky in magnitudes
    m = S.to_mag(Bw)
    out["world"]["pop_median_mag"] = wmedian(m[pop > 0], pop[pop > 0])

    # countries
    ctry = {c["i"]: c for c in areas["countries"]}
    idx = cid.ravel(); P = pop.ravel(); Bf = Bw.ravel(); Af = (area * land).ravel(); Lf = (rad * cnt).ravel()
    rows = []
    for i, c in ctry.items():
        sel = idx == i
        if not sel.any(): continue
        p = P[sel]; b = Bf[sel]; a = Af[sel]
        sp = shares(b, p); sa = shares(b, a)
        if not sa: continue
        rows.append(dict(iso3=c["iso3"], name=c["name"], continent=c["continent"], pop=float(p.sum()), land_km2=float(a.sum()), light_sum=float(Lf[sel].sum()),
                         **{f"pop_{k}": (sp or {}).get(k) for k in ["le_pristine"] + TK},
                         **{f"land_{k}": sa.get(k) for k in ["le_pristine"] + TK},
                         pop_median_mag=wmedian(S.to_mag(b[p > 0]), p[p > 0]) if p.sum() > 0 else None,
                         land_median_mag=wmedian(S.to_mag(b[a > 0]), a[a > 0])))
    # Falchi et al. Table 2 for comparison
    import gzip
    F = json.load(gzip.open(os.path.join(os.environ.get("DS_DATA", "/home/claude/hist/_data18/dark-skies"), "darkskies_falchi_tables.json.gz")))
    fal = {}
    for r in F["table2_country"][3:]:
        if len(r) != 13: continue
        try: vals = [float(x) for x in r[1:]]
        except Exception: continue
        fal[r[0].rstrip("*").strip()] = vals
    alias = {"United States of America": "United States", "Czechia": "Czech Republic", "Republic of Serbia": "Serbia", "eSwatini": "Swaziland",
             "Bosnia and Herz.": "Bosnia and Herzegovina", "Dem. Rep. Congo": "Democratic Republic of the Congo", "Russia": "Russian Federation",
             "North Macedonia": "Macedonia", "United Republic of Tanzania": "Tanzania", "The Bahamas": "Bahamas", "South Korea": "South Korea",
             "Ivory Coast": "Côte d'Ivoire", "Republic of the Congo": "Congo"}
    for r in rows:
        f = fal.get(r["name"]) or fal.get(alias.get(r["name"], "")) or None
        r["falchi_pop_milky_way"] = f[4] / 100 if f else None
        r["falchi_pop_polluted"] = f[2] / 100 if f else None
        r["falchi_land_milky_way"] = f[10] / 100 if f else None
    rows.sort(key=lambda r: -r["pop"])
    out["falchi_world"] = dict(zip(["le1.7", "gt1.7", "gt14", "gt87", "gt688", "gt3000"], [v / 100 for v in fal["World"][:6]])) if "World" in fal else None
    out["falchi_world_land"] = dict(zip(["le1.7", "gt1.7", "gt14", "gt87", "gt688", "gt3000"], [v / 100 for v in fal["World"][6:]])) if "World" in fal else None
    big = [r for r in rows if r["pop"] >= 1e6 and r["falchi_pop_milky_way"] is not None and r["pop_milky_way"] is not None]
    if big:
        a = np.array([r["pop_milky_way"] for r in big]); b = np.array([r["falchi_pop_milky_way"] for r in big])
        from scipy.stats import spearmanr
        out["falchi_compare"] = dict(n=len(big), spearman=float(spearmanr(a, b).correlation), pearson=float(np.corrcoef(a, b)[0, 1]),
                                     mean_diff=float(np.mean(a - b)), median_abs_diff=float(np.median(np.abs(a - b))))
    with open(os.path.join(D, "countries.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader()
        for r in rows: w.writerow({k: (R(v) if isinstance(v, float) else v) for k, v in r.items()})
    out["countries"] = rows

    # cities of a million or more (GeoNames)
    zf = zipfile.ZipFile(GEON); txt = io.TextIOWrapper(zf.open("cities15000.txt"), encoding="utf-8")
    cities = []
    for ln in txt:
        f = ln.rstrip("\n").split("\t")
        if f[7] in ("PPLX",): continue
        p = int(f[14] or 0)
        if p >= 100000: cities.append(dict(name=f[1].replace("\u2013", "-").replace("\u2014", "-"), lat=float(f[4]), lon=float(f[5]), cc=f[8], pop=p))
    landmask = land
    crow = []
    for c in cities:
        if not (-60 < c["lat"] < 76): continue
        b = cell(Bw, 90, -180, WC, c["lat"], c["lon"])
        rec = dict(name=c["name"], cc=c["cc"], pop=c["pop"], lat=c["lat"], lon=c["lon"], sky=b, mag=float(S.to_mag(b)) if b is not None else None)
        if c["pop"] >= 1_000_000:
            n1 = nearest_below(Bw, 90, -180, WC, c["lat"], c["lon"], TH["milky_way"], 900, landmask)
            n2 = nearest_below(Bw, 90, -180, WC, c["lat"], c["lon"], TH["polluted"], 1500, landmask)
            rec.update(mw_km=n1[0] if n1 else None, mw_lat=n1[1] if n1 else None, mw_lon=n1[2] if n1 else None,
                       dark_km=n2[0] if n2 else None, dark_lat=n2[1] if n2 else None, dark_lon=n2[2] if n2 else None)
        crow.append(rec)
    crow.sort(key=lambda r: -r["pop"])
    with open(os.path.join(D, "cities.csv"), "w", newline="") as fh:
        keys = ["name", "cc", "pop", "lat", "lon", "sky", "mag", "mw_km", "mw_lat", "mw_lon", "dark_km", "dark_lat", "dark_lon"]
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in crow: w.writerow({k: (R(r.get(k)) if isinstance(r.get(k), float) else r.get(k)) for k in keys})
    out["cities"] = crow

    # ---------- UK ----------
    zu = np.load(os.path.join(W, "uk.npz")); upop = zu["pop"]; ucnt = zu["cnt"]
    U = {y: np.load(os.path.join(W, f"uk_sky_{y}.npz"))["sky"].astype(np.float32) for y in (2015, 2019, 2023)}
    B = U[2023]; uid = np.load(os.path.join(W, "uk_area.npz"))["uid"]; lid = np.load(os.path.join(W, "uk_ltla.npz"))["lid"]
    UH, UW = B.shape; ulat = 61 - (np.arange(UH) + .5) * UC
    uarea = np.broadcast_to(S.cell_area_km2(ulat, UC)[:, None], B.shape)
    ukl = uid > 0
    rr = ((90 - (61 - (np.arange(UH) + .5) * UC)) * 24).astype(int); cc = ((-11 + (np.arange(UW) + .5) * UC + 180) * 24).astype(int)
    gbr = [c["i"] for c in areas["countries"] if c["iso3"] == "GBR"]
    cu = cid[rr][:, cc]
    anyland = ukl | ((cu > 0) & ~np.isin(cu, gbr))   # UK areas (1 km) plus other countries' land (Ireland, France) for distance searches
    nat = {}
    for a in areas["uk"]: nat.setdefault(a["nation"], []).append(a["i"])
    out["uk"] = dict(pop=shares(B[ukl], upop[ukl]), land=shares(B[ukl], uarea[ukl]), pop_total=float(upop[ukl].sum()),
                     land_km2=float(uarea[ukl].sum()), pop_median_mag=wmedian(S.to_mag(B[ukl & (upop > 0)]), upop[ukl & (upop > 0)]),
                     land_median_mag=wmedian(S.to_mag(B[ukl]), uarea[ukl]))
    out["uk"]["nations"] = {}
    for n, ids in nat.items():
        sel = np.isin(uid, ids)
        out["uk"]["nations"][n] = dict(pop=shares(B[sel], upop[sel]), land=shares(B[sel], uarea[sel]),
                                       land_median_mag=wmedian(S.to_mag(B[sel]), uarea[sel]))
    # coarse versus fine: the same UK population on the 2.5' world grid, to show the effect of resolution
    ukc = np.isin(cid, [c["i"] for c in areas["countries"] if c["iso3"] == "GBR"])
    out["uk"]["coarse_pop"] = shares(Bw[ukc], pop[ukc])
    # counties and districts
    arows = []
    for a in areas["uk"]:
        sel = uid == a["i"]
        if not sel.any(): continue
        b = B[sel]; p = upop[sel]; ar = uarea[sel]
        sp = shares(b, p); sa = shares(b, ar)
        b15 = U[2015][sel]
        r15 = float((zu["rad_2015"][sel]).sum()); r23 = float((zu["rad_2023"][sel]).sum())
        arows.append(dict(name=a["name"], nation=a["nation"], pop=float(p.sum()), land_km2=float(ar.sum()),
                          land_median_mag=wmedian(S.to_mag(b), ar), pop_median_mag=wmedian(S.to_mag(b[p > 0]), p[p > 0]) if p.sum() > 0 else None,
                          land_mw_visible=1 - sa["milky_way"], pop_mw_visible=1 - sp["milky_way"] if sp else None,
                          land_not_polluted=1 - sa["polluted"], darkest_mag=float(S.to_mag(b.min())),
                          sky_change_pct=float((np.average(b, weights=ar) / np.average(b15, weights=ar) - 1) * 100),
                          light_change_pct=float((r23 / r15 - 1) * 100) if r15 > 0 else None))
    arows.sort(key=lambda r: -r["land_median_mag"])
    with open(os.path.join(D, "uk_areas.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(arows[0].keys())); w.writeheader()
        for r in arows: w.writerow({k: (R(v) if isinstance(v, float) else v) for k, v in r.items()})
    out["uk_areas"] = arows
    lrows = []
    for a in areas["ltla"]:
        sel = lid == a["i"]
        if sel.sum() < 4: continue
        b = B[sel]; p = upop[sel]; ar = uarea[sel]; sp = shares(b, p)
        lrows.append(dict(code=a["code"], name=a["name"], pop=float(p.sum()), land_median_mag=wmedian(S.to_mag(b), ar),
                          pop_median_mag=wmedian(S.to_mag(b[p > 0]), p[p > 0]) if p.sum() > 0 else None,
                          pop_mw_visible=1 - sp["milky_way"] if sp else None, land_mw_visible=1 - shares(b, ar)["milky_way"]))
    lrows.sort(key=lambda r: -r["land_median_mag"])
    with open(os.path.join(D, "uk_councils.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(lrows[0].keys())); w.writeheader()
        for r in lrows: w.writerow({k: (R(v) if isinstance(v, float) else v) for k, v in r.items()})
    out["uk_councils"] = lrows

    # towns and cities (OS Open Names, Great Britain) and Northern Ireland towns (GeoNames)
    towns = []
    with open(OSN, encoding="utf-8") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for r in rd:
            if r["local_type"] not in ("City", "Town", "Village", "Hamlet"): continue
            la, lo = float(r["lat"]), float(r["lon"]); b = cell(B, 61, -11, UC, la, lo)
            if b is None: continue
            nm = f'{r["name2"]} ({r["name1"]})' if r["lang1"] in ("cym", "gla") and r["name2"] else r["name1"]
            towns.append(dict(name=nm, kind=r["local_type"], county=r["county"] or r["district"], region=r["region"], lat=la, lon=lo, sky=b))
    for c in cities:
        pass
    zf = zipfile.ZipFile(GEON); txt = io.TextIOWrapper(zf.open("cities15000.txt"), encoding="utf-8")
    for ln in txt:
        f = ln.rstrip("\n").split("\t")
        if f[8] == "GB" and f[10] == "NIR":
            la, lo = float(f[4]), float(f[5]); b = cell(B, 61, -11, UC, la, lo)
            towns.append(dict(name=f[1].replace("\u2013", "-").replace("\u2014", "-"), kind="City" if int(f[14] or 0) >= 100000 else "Town", county="", region="Northern Ireland", lat=la, lon=lo, sky=b))
    for t in towns: t["mag"] = float(S.to_mag(t["sky"]))
    with open(os.path.join(D, "uk_towns.csv"), "w", newline="") as fh:
        keys = ["name", "kind", "county", "region", "lat", "lon", "sky", "mag"]
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader()
        for r in towns: w.writerow({k: (R(r[k]) if isinstance(r[k], float) else r[k]) for k in keys})
    out["uk_towns"] = {k: sum(1 for t in towns if t["kind"] == k) for k in ("City", "Town", "Village", "Hamlet")}
    tw = [t for t in towns if t["kind"] in ("Town", "City")]
    out["uk_towns_darkest"] = sorted(tw, key=lambda t: t["sky"])[:25]
    out["uk_towns_brightest"] = sorted(tw, key=lambda t: -t["sky"])[:10]
    out["uk_villages_darkest"] = sorted([t for t in towns if t["kind"] == "Village"], key=lambda t: t["sky"])[:15]
    out["uk_town_mw_visible"] = {k: float(np.mean([t["sky"] < TH["milky_way"] for t in towns if t["kind"] == k])) for k in ("City", "Town", "Village", "Hamlet")}
    # UK cities: nearest Milky Way sky and nearest unpolluted sky (on land)
    ukcities = []
    for c in cities:
        if c["cc"] in ("GB", "IE", "IM") and 49.8 < c["lat"] < 61 and -11 < c["lon"] < 2 and c["pop"] >= 100000:
            n1 = nearest_below(B, 61, -11, UC, c["lat"], c["lon"], TH["milky_way"], 300, anyland)
            n2 = nearest_below(B, 61, -11, UC, c["lat"], c["lon"], TH["nat_lost"], 400, anyland)
            ukcities.append(dict(name=c["name"], cc=c["cc"], pop=c["pop"], lat=c["lat"], lon=c["lon"], sky=cell(B, 61, -11, UC, c["lat"], c["lon"]),
                                 mw_km=n1[0] if n1 else None, mw_lat=n1[1] if n1 else None, mw_lon=n1[2] if n1 else None,
                                 dark_km=n2[0] if n2 else None, dark_lat=n2[1] if n2 else None, dark_lon=n2[2] if n2 else None))
    ukcities.sort(key=lambda r: -r["pop"]); out["uk_cities"] = ukcities

    # Dark Sky Places
    dsp = list(csv.DictReader(open(os.path.join(D, "dark_sky_places.csv"))))
    for r in dsp:
        if r["lat"] == "": r["sky_model"] = ""; continue
        la, lo = float(r["lat"]), float(r["lon"])
        b = cell(B, 61, -11, UC, la, lo) if (49.8 < la < 61 and -11 < lo < 2) else cell(Bw, 90, -180, WC, la, lo)
        r["sky_model"] = R(b) if b is not None and R(b) is not None else ""
    with open(os.path.join(D, "dark_sky_places.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(dsp[0].keys())); w.writeheader(); w.writerows(dsp)
    ukd = [r for r in dsp if r["sky_model"] != "" and 49.8 < float(r["lat"]) < 61 and -11 < float(r["lon"]) < 2]
    out["uk_dsp"] = [dict(name=r["name"], status=r["status"], year=r["year"], lat=float(r["lat"]), lon=float(r["lon"]), sky=float(r["sky_model"]),
                          mag=float(S.to_mag(float(r["sky_model"])))) for r in ukd]
    wd = [r for r in dsp if r["sky_model"] != ""]
    out["dsp_world"] = dict(n=len(dsp), placed=len(wd), mw_visible=float(np.mean([float(r["sky_model"]) < TH["milky_way"] for r in wd])),
                            not_polluted=float(np.mean([float(r["sky_model"]) < TH["polluted"] for r in wd])))
    # land share of the UK below each Dark Sky Place's sky
    # change in light 2015 to 2023
    ch = {}
    for y in (2015, 2019, 2023):
        ch[y] = dict(rad=float(zu[f"rad_{y}"][ukl].sum()), pop_mw=shares(U[y][ukl], upop[ukl])["milky_way"],
                     land_mw=shares(U[y][ukl], uarea[ukl])["milky_way"], land_polluted=shares(U[y][ukl], uarea[ukl])["polluted"])
    out["uk_change"] = ch
    d = U[2023][ukl] / U[2015][ukl]
    out["uk_change"]["land_brighter"] = float(np.average(d > 1.05, weights=uarea[ukl]))
    out["uk_change"]["land_dimmer"] = float(np.average(d < 1 / 1.05, weights=uarea[ukl]))
    hdr = json.load(open(os.path.join(W, "bundle_header.json")))
    out["bundle"] = {k: v for k, v in hdr.items() if k in ("uk_sums", "retrieved", "source")}
    json.dump(out, open(os.path.join(W, "stats.json"), "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("world", "uk")}, indent=1, default=float)[:3000])
