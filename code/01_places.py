"""Step 1. Dark Sky Places and Globe at Night observations.
Reads the two browser bundles in DS_DATA (default /home/claude/hist/_data18/dark-skies):
  darkskies_places_wiki.json.gz : English Wikipedia "Dark-sky preserve" wikitext (CC BY-SA 4.0), coordinates of the
                                  pages it links to (MediaWiki API), and Wikidata items of dark-sky place classes (CC0)
  darkskies_gan.json.gz         : Globe at Night campaign data 2006 to 2025 (NOIRLab, CC BY 4.0)
Writes data/dark_sky_places.csv and work/gan_sqm.csv (clean Sky Quality Meter readings).
Run: python3 code/01_places.py
"""
import csv, gzip, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
DATA = os.environ.get("DS_DATA", "/home/claude/hist/_data18/dark-skies")
W = os.path.join(ROOT, "work"); D = os.path.join(ROOT, "data")
os.makedirs(W, exist_ok=True); os.makedirs(D, exist_ok=True)


def strip(s):
    s = re.sub(r"<ref[^>]*/>", "", s); s = re.sub(r"<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+[\u2013\u2014]\s+", ", ", s).replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", s).strip()


def first_link(s):
    m = re.search(r"\[\[([^|\]#]+)", s)
    return m.group(1).strip() if m else None


def places():
    b = json.load(gzip.open(os.path.join(DATA, "darkskies_places_wiki.json.gz")))
    co = b["link_coords"]; red = {r["from"]: r["to"] for r in b["redirects"]}
    def coord(title):
        if not title: return None
        title = title[0].upper() + title[1:]
        t = red.get(title, title)
        c = co.get(t, {}).get("c")
        return c
    t = b["wikitext"]["Dark-sky preserve"]
    s = t.index("{| class=\"wikitable sortable\"", 0); e = t.index("|}", s)
    out = []
    for row in t[s:e].split("\n|-")[1:]:
        cells = [c for c in re.split(r"\n\s*\|", "\n" + row.strip()) if c is not None][1:]
        if len(cells) < 6: continue
        flags = re.findall(r"\{\{[Ff]lag\|([^}|]+)", cells[0])
        country = " / ".join(flags) if flags else strip(cells[0])
        name = strip(cells[1]); loc = strip(cells[2]); status = strip(cells[5]); note = strip(cells[6]) if len(cells) > 6 else ""
        yr = re.search(r"(19|20)\d\d", note); year = int(yr.group(0)) if yr else None
        nl, ll = first_link(cells[1]), first_link(cells[2])
        c = coord(nl); src = "Wikipedia article of the place (" + nl + ")" if c else None
        # no fallback to the location column: a region's centre (e.g. "Scotland") is not a place
        out.append(dict(name=name, country=country, location=loc, status=status, year=year,
                        lat=round(c[0], 4) if c else "", lon=round(c[1], 4) if c else "", coord_source=src or "none"))
    # Wikidata items that the table does not name (by label), with their own coordinates
    names = {o["name"].lower() for o in out}
    lines = b["wikidata_tsv"].strip().split("\n")[1:]
    seen = set()
    for ln in lines:
        f = ln.split("\t")
        if len(f) < 6: continue
        lab = strip(re.sub(r'^"|"@en$', "", f[1])); m = re.search(r"POINT\(([-\d.]+) ([-\d.]+)\)", f[3])
        if not m or not lab or lab.lower() in names or lab in seen: continue
        seen.add(lab)
        out.append(dict(name=lab, country=re.sub(r'^"|"@en$', "", f[5]), location="", status="dark-sky place (Wikidata)", year=None,
                        lat=round(float(m.group(2)), 4), lon=round(float(m.group(1)), 4), coord_source="Wikidata P625 (" + f[0].strip("<>").split("/")[-1] + ")"))
    with open(os.path.join(D, "dark_sky_places.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("places", len(out), "with coords", sum(1 for o in out if o["lat"] != ""))


def gan():
    b = json.load(gzip.open(os.path.join(DATA, "darkskies_gan.json.gz")))
    sq, lm = [], []
    for r in b["rows"]:
        lat, lon, date, lt, ut, lim, sqm, cloud, country, typ, el = r
        try: lat, lon = float(lat), float(lon)
        except Exception: continue
        if (lat == 0 and lon == 0) or not (-90 < lat < 90 and -180 <= lon <= 180): continue
        year = int(date[:4]) if date[:4].isdigit() else None
        try: h = int(lt.split(":")[0])
        except Exception: h = None
        dark_hour = h is not None and (h >= 20 or h <= 4)
        if cloud != "clear" or not dark_hour or year is None: continue
        try: v = float(sqm)
        except Exception: v = None
        if v is not None and 15.0 <= v <= 22.4:
            sq.append([round(lat, 5), round(lon, 5), year, v, typ, country])
        try: l = int(float(lim))
        except Exception: l = None
        if l is not None and 0 <= l <= 7 and typ == "GAN":
            lm.append([round(lat, 5), round(lon, 5), year, l, country])
    with open(os.path.join(W, "gan_sqm.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["lat", "lon", "year", "sqm", "type", "country"]); w.writerows(sq)
    print("gan sqm", len(sq))


if __name__ == "__main__":
    places(); gan()
