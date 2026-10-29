"""Step 2. Unpack the WorldPop bundle into model grids, and rasterise countries and UK areas.

Input DS_DATA/darkskies_worldpop.bin.gz, made in the browser from WorldPop files (CC BY 4.0):
  * Night-time lights 2015 to 2023, flares and volcanoes filtered (WorldPop covariates, DOI 10.5258/SOTON/WP00772),
    3 arc second per-country GeoTIFFs of the Earth Observation Group's annual VIIRS VNL v2.1/2.2 radiance
    (nW/cm2/sr). World 2023: every country file averaged to a 2.5 arc minute grid (mean of valid pixels, and their
    count). UK and Ireland 2015 to 2023: GBR, IRL and IMN files averaged to 30 arc seconds.
  * Population 2023, constrained, 30 arc seconds (WorldPop Global2 R2025A, DOI 10.5258/SOTON/WP00845), summed to the
    2.5 arc minute grid and kept at 30 arc seconds for the UK box.
Format: 4-byte header length, JSON header, then raw little-endian arrays at the offsets listed in the header.
Writes work/world.npz, work/uk.npz, work/world_country.npz (Natural Earth admin 0 index per cell) and
work/uk_area.npz, work/uk_ltla.npz (UK county or NI district index per 30" cell), plus work/areas.json.
Run: python3 code/02_grids.py
"""
import gzip, json, os, struct
import sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DATA = os.environ.get("DS_DATA", "/home/claude/hist/_data18/dark-skies")
W = os.path.join(ROOT, "work")
sys.path.insert(0, HERE)
from skyglow import f16_coarse
NE = "/home/claude/hist/_data3/ne/geojson/ne_10m_admin_0_countries.geojson"
UKC = "/home/claude/hist/how-roman-is-your-road/data/counties.geojson"
LTLA = "/home/claude/hist/how-roman-is-your-road/data/ons/ltla.geojson"
WG = dict(W=8640, H=4320, lon0=-180.0, lat0=90.0, cell=1 / 24)
UG = dict(W=1560, H=1344, lon0=-11.0, lat0=61.0, cell=1 / 120)


def read_bundle():
    raw = gzip.open(os.path.join(DATA, "darkskies_worldpop.bin.gz")).read()
    n = struct.unpack("<I", raw[:4])[0]; hdr = json.loads(raw[4:4 + n]); base = 4 + n
    arrs = {}
    for a in hdr["arrays"]:
        b = raw[base + a["offset"]: base + a["offset"] + a["nbytes"]]
        arrs[a["name"]] = np.frombuffer(b, dtype=np.dtype(a["dtype"]).newbyteorder("<")).reshape(a["shape"]).copy()
    return hdr, arrs


def rings(geom):
    if geom["type"] == "GeometryCollection":
        return [p for g in geom["geometries"] if g["type"] in ("Polygon", "MultiPolygon") for p in rings(g)]
    cs = geom["coordinates"]
    return [cs] if geom["type"] == "Polygon" else cs


def rasterise(feats, G):
    """Index raster (0 = none, i+1 = feature i): each cell takes the polygon drawn over it (PIL fill, cell centres)."""
    img = Image.new("I", (G["W"], G["H"]), 0); d = ImageDraw.Draw(img)
    px = lambda lon, lat: ((lon - G["lon0"]) / G["cell"] - .5, (G["lat0"] - lat) / G["cell"] - .5)
    for i, f in enumerate(feats):
        for poly in rings(f["geometry"]):
            d.polygon([px(*c[:2]) for c in poly[0]], fill=i + 1)
            for hole in poly[1:]:
                d.polygon([px(*c[:2]) for c in hole], fill=0)
    return np.array(img, dtype=np.int32)


if __name__ == "__main__":
    hdr, A = read_bundle()
    json.dump({k: v for k, v in hdr.items() if k != "arrays"}, open(os.path.join(W, "bundle_header.json"), "w"), indent=1)
    rad = A["world_mean"].astype(np.float32); cnt = A["world_cnt"].astype(np.float32); pop = A["world_pop"].astype(np.float32)
    rad[~np.isfinite(rad)] = 0
    np.savez_compressed(os.path.join(W, "world.npz"), rad=f16_coarse(rad), cnt=cnt.astype(np.uint16), pop=np.round(pop, 1).astype(np.float32))
    years = [int(k.split("_")[-1]) for k in A if k.startswith("uk_rad_")]
    np.savez_compressed(os.path.join(W, "uk.npz"), cnt=A["uk_cnt"].astype(np.float32), pop=A["uk_pop"].astype(np.float32),
                        **{f"rad_{y}": A[f"uk_rad_{y}"].astype(np.float32) for y in years})
    print("world land cells", int((cnt > 0).sum()), "pop", float(pop.sum()), "uk years", years)

    ne = json.load(open(NE))["features"]
    ne = [f for f in ne if f["geometry"]]
    cid = rasterise(ne, WG)
    np.savez_compressed(os.path.join(W, "world_country.npz"), cid=cid.astype(np.int16))
    areas = {"countries": [dict(i=i + 1, iso3=(f["properties"].get("ISO_A3") if f["properties"].get("ISO_A3") not in (None, "-99") else f["properties"].get("ADM0_A3")),
                                name=f["properties"].get("NAME"), continent=f["properties"].get("CONTINENT")) for i, f in enumerate(ne)]}
    uk = json.load(open(UKC))["features"]
    ni = [f for f in json.load(open(LTLA))["features"] if f["properties"]["areacd"].startswith("N")]
    feats = [dict(geometry=f["geometry"], name=f["properties"]["county"], nation=f["properties"]["nation"]) for f in uk] + \
            [dict(geometry=f["geometry"], name=f["properties"]["areanm"], nation="Northern Ireland") for f in ni]
    uid = rasterise(feats, UG)
    np.savez_compressed(os.path.join(W, "uk_area.npz"), uid=uid.astype(np.int16))
    lt = json.load(open(LTLA))["features"]
    lid = rasterise(lt, UG)
    np.savez_compressed(os.path.join(W, "uk_ltla.npz"), lid=lid.astype(np.int16))
    areas["uk"] = [dict(i=i + 1, name=f["name"], nation=f["nation"]) for i, f in enumerate(feats)]
    areas["ltla"] = [dict(i=i + 1, code=f["properties"]["areacd"], name=f["properties"]["areanm"]) for i, f in enumerate(lt)]
    json.dump(areas, open(os.path.join(W, "areas.json"), "w"), ensure_ascii=False)
    print("countries", len(ne), "uk areas", len(feats), "ltla", len(lt))
