"""Step 6. data/results.json (every number used anywhere) and work/page_data.json (tables the page embeds).
Run: python3 code/06_results.py
"""
import csv, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
W = os.path.join(ROOT, "work"); D = os.path.join(ROOT, "data")
ST = json.load(open(os.path.join(W, "stats.json")))
MO = json.load(open(os.path.join(W, "model.json")))
AR = json.load(open(os.path.join(W, "areas.json")))
HD = json.load(open(os.path.join(W, "bundle_header.json")))
r4 = lambda x: None if x is None else round(float(x), 4)
r1 = lambda x: None if x is None else round(float(x), 1)


def sh(s, pre=""):
    if not s: return {}
    return {pre + "mw": r4(s["milky_way"]), pre + "polluted": r4(s["polluted"]), pre + "unpolluted": r4(1 - s["polluted"]),
            pre + "pristine": r4(s["le_pristine"]), pre + "nat_lost": r4(s["nat_lost"]), pre + "no_dark": r4(s["no_dark_adapt"]),
            pre + "mw_visible": r4(1 - s["milky_way"])}


R = {}
b = MO["best"]
R["model"] = dict(alpha=MO["alpha"], L=MO["L"], k=MO["k"], d0=MO["d0"], r_max=MO["r_max"], natural=MO["natural"],
                  n_fit=b["cv"]["n"], cv_rmse=r4(b["cv"]["rmse"]), cv_mae=r4(b["cv"]["mae"]), cv_bias=r4(b["cv"]["bias"]), cv_r=r4(b["cv"]["r"]),
                  mae_fit=r4(b["mae_fit"]), cv18_mae=r4(b["cv18"]["mae"]), cv18_rmse=r4(b["cv18"]["rmse"]), cv18_bias=r4(b["cv18"]["bias"]), cv18_r=r4(b["cv18"]["r"]), n18=b["cv18"]["n"],
                  fit_min=MO["fit_min"], err_by_obs={k: dict(n=v["n"], err=r4(v["median_err"])) for k, v in MO["err_by_obs"].items()},
                  grid=[dict(alpha=g["alpha"], L=g["L"], cv18_mae=r4(g["cv18"]["mae"]), cv_rmse=r4(g["cv"]["rmse"]), cv_r=r4(g["cv"]["r"])) for g in MO["grid"]],
                  older=dict(n=MO["older_readings"]["n"], rmse=r4(MO["older_readings"]["rmse"]), bias=r4(MO["older_readings"]["bias"]), r=r4(MO["older_readings"]["r"])),
                  uk_fine={k: r4(v) for k, v in (MO["uk_points"]["fine"] or {}).items()}, uk_coarse={k: r4(v) for k, v in (MO["uk_points"]["coarse"] or {}).items()})
w = ST["world"]
R["world"] = dict(**sh(w["pop"], "pop_"), **sh(w["land"], "land_"), pop_total_bn=r4(w["pop_total"] / 1e9), land_km2=round(w["land_km2"]),
                  pop_median_mag=r4(w["pop_median_mag"]), people_mw_bn=r4(w["pop"]["milky_way"] * w["pop_total"] / 1e9))
fw, fl = ST["falchi_world"], ST["falchi_world_land"]
R["falchi"] = dict(mean_diff_pts=round(ST["falchi_compare"]["mean_diff"] * 100), pop_mw=fw["gt688"], pop_polluted=fw["gt14"], pop_no_dark=fw["gt3000"], land_polluted=fl["gt14"], land_mw=fl["gt688"],
                   compare={k: r4(v) if isinstance(v, float) else v for k, v in ST.get("falchi_compare", {}).items()})
# countries
C = ST["countries"]
ISOS = {x["c"] for x in HD["world_log"]}
nolight = lambda c: c["iso3"] not in ISOS and (c["pop_milky_way"] or 0) == 0   # no light file of its own in the WorldPop set
R["countries_no_lights"] = [c["name"] for c in C if nolight(c) and c["pop"] >= 1e6]
Cbig = [c for c in C if c["pop"] >= 1e6 and c["pop_milky_way"] is not None and not nolight(c)]
R["countries_n"] = len(Cbig)
R["country"] = {c["iso3"]: dict(name=c["name"], pop_m=r1(c["pop"] / 1e6), pop_mw=r4(c["pop_milky_way"]), land_mw=r4(c["land_milky_way"]),
                                land_unpolluted=r4(1 - c["land_polluted"]), pop_unpolluted=r4(1 - c["pop_polluted"]) if c["pop_polluted"] is not None else None,
                                falchi_pop_mw=c["falchi_pop_milky_way"], pop_mag=r4(c["pop_median_mag"]))
                for c in Cbig}
srt = sorted(Cbig, key=lambda c: -c["pop_milky_way"])
R["countries_brightest"] = [dict(iso3=c["iso3"], name=c["name"], pop_mw=r4(c["pop_milky_way"])) for c in srt[:12]]
R["countries_darkest"] = [dict(iso3=c["iso3"], name=c["name"], pop_mw=r4(c["pop_milky_way"]), pop_m=r1(c["pop"] / 1e6)) for c in srt[::-1][:12]]
R["countries_mw_over_half"] = sum(1 for c in Cbig if c["pop_milky_way"] > .5)
R["countries_mw_over_90"] = sum(1 for c in Cbig if c["pop_milky_way"] > .9)
# cities
def dedupe(rows, km):
    """Keep a city only if no larger kept city lies within km (GeoNames lists boroughs such as Queens or Islington as cities)."""
    keep = []
    for c in sorted(rows, key=lambda c: -c["pop"]):
        if all((c["lat"] - k["lat"]) ** 2 + ((c["lon"] - k["lon"]) * np.cos(np.radians(c["lat"]))) ** 2 > (km / 111.2) ** 2 for k in keep): keep.append(c)
    return keep
cities = dedupe([c for c in ST["cities"] if c.get("mw_km") is not None], 25)
R["megacities"] = [dict(name=c["name"], cc=c["cc"], pop_m=r1(c["pop"] / 1e6), mw_km=round(c["mw_km"]), dark_km=round(c["dark_km"]) if c.get("dark_km") else None)
                   for c in sorted(cities, key=lambda c: -c["pop"])[:40]]
far = sorted(cities, key=lambda c: -c["mw_km"])
R["cities_farthest"] = [dict(name=c["name"], cc=c["cc"], pop_m=r1(c["pop"] / 1e6), mw_km=round(c["mw_km"])) for c in far[:12]]
R["cities_1m_n"] = len(cities)
R["cities_1m_median_mw_km"] = round(float(np.median([c["mw_km"] for c in cities])))
R["cities_1m_mw_under_50"] = sum(1 for c in cities if c["mw_km"] < 50)
# UK
U = ST["uk"]
R["uk"] = dict(**sh(U["pop"], "pop_"), **sh(U["land"], "land_"), pop_m=r1(U["pop_total"] / 1e6), land_km2=round(U["land_km2"]),
               pop_median_mag=r4(U["pop_median_mag"]), land_median_mag=r4(U["land_median_mag"]), coarse_pop_mw=r4(U["coarse_pop"]["milky_way"]),
               people_mw_m=r1(U["pop"]["milky_way"] * U["pop_total"] / 1e6), people_mw_visible_m=r1((1 - U["pop"]["milky_way"]) * U["pop_total"] / 1e6))
R["uk"]["nations"] = {n: dict(**sh(v["pop"], "pop_"), **sh(v["land"], "land_"), land_median_mag=r4(v["land_median_mag"])) for n, v in U["nations"].items()}
A = ST["uk_areas"]
R["uk_area"] = {a["name"]: dict(nation=a["nation"], land_mag=r4(a["land_median_mag"]), pop_mag=r4(a["pop_median_mag"]), land_mw_visible=r4(a["land_mw_visible"]),
                                pop_mw_visible=r4(a["pop_mw_visible"]), land_unpolluted=r4(a["land_not_polluted"]), darkest_mag=r4(a["darkest_mag"]),
                                sky_change_pct=r1(a["sky_change_pct"]), light_change_pct=r1(a["light_change_pct"]), pop_k=round(a["pop"] / 1e3))
                for a in A}
lc = sorted([a for a in A if a["light_change_pct"] is not None], key=lambda a: a["light_change_pct"])
R["uk_light_fall"] = [dict(name=a["name"], pct=r1(a["light_change_pct"])) for a in lc[:5]]
R["uk_light_rise"] = [dict(name=a["name"], pct=r1(a["light_change_pct"])) for a in lc[::-1][:5]]
R["uk_areas_light_up"] = sum(1 for a in lc if a["light_change_pct"] > 0)
R["uk_areas_darkest"] = [a["name"] for a in A[:10]]
R["uk_areas_brightest"] = [a["name"] for a in A[::-1][:10]]
R["uk_areas_n"] = len(A)
Eng = [a for a in A if a["nation"] == "England"]
R["england_darkest"] = [a["name"] for a in Eng[:5]]
R["uk_areas_pop_mw_visible_over_half"] = sum(1 for a in A if (a["pop_mw_visible"] or 0) > .5)
L = ST["uk_councils"]
R["uk_councils_darkest"] = [dict(name=l["name"], land_mag=r4(l["land_median_mag"])) for l in L[:10]]
R["uk_councils_brightest"] = [dict(name=l["name"], land_mag=r4(l["land_median_mag"]), pop_mw_visible=r4(l["pop_mw_visible"])) for l in L[::-1][:10]]
R["uk_councils_n"] = len(L)
R["uk_councils_all_hidden"] = sum(1 for l in L if (l["pop_mw_visible"] or 0) < .01)
tw = lambda t: dict(name=t["name"], kind=t["kind"], county=t["county"], region=t["region"], mag=r4(t["mag"]), sky=r1(t["sky"]))
R["uk_towns_darkest"] = [tw(t) for t in ST["uk_towns_darkest"][:15]]
R["uk_towns_brightest"] = [tw(t) for t in ST["uk_towns_brightest"][:10]]
R["uk_villages_darkest"] = [tw(t) for t in ST["uk_villages_darkest"][:10]]
R["uk_places_n"] = ST["uk_towns"]
R["uk_kind_mw_visible"] = {k: r4(v) for k, v in ST["uk_town_mw_visible"].items()}
R["uk_cities"] = {c["name"]: dict(pop_k=round(c["pop"] / 1e3), sky=r1(c["sky"]), mag=r4(22 - 2.5 * np.log10((c["sky"] + 174) / 174)) if c["sky"] else None,
                                  mw_km=round(c["mw_km"]) if c["mw_km"] is not None else None, mw_lat=r4(c["mw_lat"]), mw_lon=r4(c["mw_lon"]),
                                  dark_km=round(c["dark_km"]) if c["dark_km"] is not None else None, cc=c["cc"]) for c in ST["uk_cities"]}
# nearest named town or village to each UK city's nearest Milky Way sky (OS Open Names / GeoNames)
TW = [r for r in csv.DictReader(open(os.path.join(D, "uk_towns.csv"))) if r["kind"] in ("Town", "Village")]
twa = np.array([[float(r["lat"]), float(r["lon"])] for r in TW])
def near(la, lo):
    if la is None: return None
    d = (twa[:, 0] - la) ** 2 + ((twa[:, 1] - lo) * np.cos(np.radians(la))) ** 2; k = int(np.argmin(d)); r = TW[k]
    return dict(name=r["name"], county=r["county"], km=round(float(np.sqrt(d[k]) * 111.2), 1))
ST["uk_cities"] = dedupe(ST["uk_cities"], 12)
R["uk_cities"] = {k: v for k, v in R["uk_cities"].items() if k in {c["name"] for c in ST["uk_cities"]}}
for n, c in R["uk_cities"].items():
    c["mw_near"] = near(c["mw_lat"], c["mw_lon"])
# selected world cities by name (largest of each name)
R["city"] = {}
for c in sorted(cities, key=lambda c: -c["pop"]):
    if c["name"] not in R["city"]:
        R["city"][c["name"]] = dict(cc=c["cc"], pop_m=r1(c["pop"] / 1e6), mw_km=round(c["mw_km"]), dark_km=round(c["dark_km"]) if c.get("dark_km") else None)
# Dark Sky Places
R["dsp_uk"] = [dict(name=d["name"], status=d["status"], year=d["year"], mag=r4(d["mag"]), sky=r1(d["sky"])) for d in sorted(ST["uk_dsp"], key=lambda d: d["sky"])]
R["dsp_uk_n"] = len(ST["uk_dsp"]); R["dsp_world"] = {k: r4(v) if isinstance(v, float) else v for k, v in ST["dsp_world"].items()}
R["dsp_uk_mw_visible"] = sum(1 for d in ST["uk_dsp"] if d["sky"] < 688)
# change
ch = ST["uk_change"]; sums = HD.get("uk_sums", {})
yrs = list(range(2015, 2024))
R["change"] = dict(years=yrs, gbr=[round(sums.get(f"GBR_{y}", 0)) for y in yrs], irl=[round(sums.get(f"IRL_{y}", 0)) for y in yrs],
                   gbr_pct=r1((sums["GBR_2023"] / sums["GBR_2015"] - 1) * 100), irl_pct=r1((sums["IRL_2023"] / sums["IRL_2015"] - 1) * 100),
                   pop_mw_2015=r4(ch["2015"]["pop_mw"]), pop_mw_2023=r4(ch["2023"]["pop_mw"]), land_mw_2015=r4(ch["2015"]["land_mw"]), land_mw_2023=r4(ch["2023"]["land_mw"]),
                   land_polluted_2015=r4(ch["2015"]["land_polluted"]), land_polluted_2023=r4(ch["2023"]["land_polluted"]),
                   land_brighter=r4(ch["land_brighter"]), land_dimmer=r4(ch["land_dimmer"]))
R["meta"] = dict(retrieved=HD.get("retrieved", "")[:10], world_files=len(HD.get("world_log", [])), uk_files=len(HD.get("uk_log", [])),
                 gan_sqm_all=sum(1 for _ in open(os.path.join(W, "gan_sqm.csv"))) - 1, dsp_rows=ST["dsp_world"]["n"])
json.dump(R, open(os.path.join(D, "results.json"), "w"), indent=1, ensure_ascii=False)

# page tables
PD = dict(ukAreaNames=[a["name"] for a in AR["uk"]],
          countries=[[c["iso3"], c["name"], round(c["pop"] / 1e6, 2), r4(c["pop_milky_way"]), c["falchi_pop_milky_way"], r4(1 - c["land_polluted"]), r4(c["pop_median_mag"])] for c in Cbig],
          areas=[[a["name"], a["nation"], round(a["pop"] / 1e3), r4(a["land_median_mag"]), r4(a["pop_mw_visible"]), r4(a["land_mw_visible"]), r4(a["land_not_polluted"]), r1(a["sky_change_pct"])] for a in A],
          cities=[[c["name"], c["cc"], round(c["pop"] / 1e6, 2), round(c["mw_km"]), round(c["dark_km"]) if c.get("dark_km") else None, c["lat"], c["lon"], r4(c["mw_lat"]), r4(c["mw_lon"])] for c in sorted(cities, key=lambda c: -c["pop"])],
          ukcities=[[c["name"], c["cc"], round(c["pop"] / 1e3), round(c["mw_km"]) if c["mw_km"] is not None else None, round(c["dark_km"]) if c["dark_km"] is not None else None, c["lat"], c["lon"], r4(c["mw_lat"]), r4(c["mw_lon"])] for c in ST["uk_cities"]],
          dsp=[[d["name"], d["status"], d["year"], r4(d["mag"]), d["lat"], d["lon"]] for d in sorted(ST["uk_dsp"], key=lambda d: d["sky"])],
          change=R["change"])
def segs(x):
    if not x: return [0] * 6
    return [r4(x["le_pristine"]), r4(1 - x["polluted"] - x["le_pristine"]), r4(x["polluted"] - x["nat_lost"]), r4(x["nat_lost"] - x["milky_way"]),
            r4(x["milky_way"] - x["no_dark_adapt"]), r4(x["no_dark_adapt"])]
PD["nations"] = {n: dict(land=segs(U["nations"][n]["land"]), pop=segs(U["nations"][n]["pop"])) for n in ("England", "Wales", "Scotland", "Northern Ireland")}
PD["nations"]["United Kingdom"] = dict(land=segs(U["land"]), pop=segs(U["pop"]))
uid = np.load(os.path.join(W, "uk_area.npz"))["uid"]
rr, cc = np.nonzero(uid)
lat = 61 - (rr + .5) / 120; lon = -11 + (cc + .5) / 120
PD["areaPts"] = {}
for a in AR["uk"]:
    m = uid[rr, cc] == a["i"]
    if m.any():
        la, lo = lat[m], lon[m]; k = np.argmin((la - la.mean()) ** 2 + ((lo - lo.mean()) * .6) ** 2)
        PD["areaPts"][a["name"]] = [round(float(la[k]), 3), round(float(lo[k]), 3)]
fit = np.load(os.path.join(W, "gan_fit.npy"))
rng = np.random.default_rng(3); idx = rng.choice(len(fit), min(1500, len(fit)), replace=False)
PD["fit"] = [[round(float(fit[i, 2]), 2), round(float(fit[i, 3]), 2)] for i in idx]
json.dump(PD, open(os.path.join(W, "page_data.json"), "w"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps({k: R[k] for k in ("model", "world", "falchi", "uk")}, indent=1)[:4000])
