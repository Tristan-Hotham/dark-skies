"""Step 11. Blog post (release/blog/post.html from code/blog_template.html), blog and Zenodo meta files, README.md
and the Zenodo folder (paper, key CSVs, results.json and a code-and-data zip).
Image placeholders {{IMG|file|alt|caption}} are left for the uploader.
Run: python3 code/11_release.py
"""
import importlib.util, json, os, re, shutil, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "07_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
NAME = "Hotham_Darkest_Skies"
DASH = ("—", "–", "--")

t = open(os.path.join(HERE, "blog_template.html")).read()
t = re.sub(r"\{\{(?!IMG\|)([^}|]+)(\|(\w+))?\}\}", b.sub, t)
assert "{{" not in t.replace("{{IMG|", "")
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in DASH: assert bad not in vis, bad
os.makedirs(os.path.join(ROOT, "release", "blog"), exist_ok=True)
open(os.path.join(ROOT, "release", "blog", "post.html"), "w").write(t)
for m in re.findall(r"\{\{IMG\|([^|]+)\|", t):
    assert os.path.exists(os.path.join(ROOT, "release", "blog", m)), m
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = dict(
    title="Darkest skies: where you can still see the Milky Way",
    slug="dark-skies",
    excerpt=(f"I modelled the glow of the world's lights from satellite images and checked it against {R['model']['n_fit']:,} sky meter readings. "
             f"By my count {round(R['world']['pop_mw'] * 100)}% of people, and {round(R['uk']['pop_mw'] * 100)}% in the UK, cannot see the Milky Way from home."),
    seo_description="A sky glow map of the world and a 1 km map of the UK: who can still see the Milky Way, the darkest counties, and how far cities are from a dark sky.",
    tags=["night sky", "light pollution", "Milky Way", "maps", "satellite data", "VIIRS", "astronomy", "data visualisation"],
    header_alt=("Title card reading 'Darkest skies' on pale paper. Below, a world map on a dark ground where city lights glow rose, amber and white, "
                "and beside it a 1 km map of Britain and Ireland in the same colours: navy dark skies over the Highlands, Wales and Northumberland, "
                "bright halos around London, the Midlands, Manchester and the Central Belt."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in DASH: assert bad not in str(v)
json.dump(meta, open(os.path.join(ROOT, "release", "blog", "meta.json"), "w"), indent=2, ensure_ascii=False)

pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex")).read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("$\\rho$", "rho").replace("\\%", "%").replace("\\&", "&").replace("$\\mu$", "µ").replace("\\,", " ").replace("~", " ")
assert "\\" not in ab and "$" not in ab, ab
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
zmeta = dict(
    title="Darkest Skies: Where You Can Still See the Milky Way. A Sky Glow Model of the World and the United Kingdom from VIIRS Night Lights, Checked Against Citizen Sky Meter Readings",
    description_html=f"<p>{ab}</p><p>Interactive version: https://maps.tristanhotham.com/dark-skies/. Data and code: https://github.com/Tristan-Hotham/dark-skies. Blog post: to follow.</p>"
                     "<p>Text, figures and derived data: CC BY 4.0, except dark_sky_places.csv (from English Wikipedia, CC BY-SA 4.0). Code: MIT. "
                     "Night lights and population: WorldPop (CC BY 4.0), from Earth Observation Group VIIRS VNL data. Sky meter readings: Globe at Night (CC BY 4.0). "
                     "Places: OS Open Names (Open Government Licence v3) and GeoNames (CC BY 4.0). Boundaries: Natural Earth (public domain) and ONS (Open Government Licence v3).</p>",
    keywords=["light pollution", "night sky brightness", "skyglow", "Milky Way", "VIIRS", "night lights", "Globe at Night", "Sky Quality Meter",
              "United Kingdom", "data visualisation"],
    licence="cc-by-4.0",
    related=[
        dict(identifier="https://github.com/Tristan-Hotham/dark-skies", relation="issupplementedby", resource_type="software"),
        dict(identifier="https://maps.tristanhotham.com/dark-skies/", relation="issupplementedby", resource_type="other"),
        dict(identifier="https://doi.org/10.5258/SOTON/WP00772", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.5258/SOTON/WP00845", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://globeatnight.org/maps-data/", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://doi.org/10.1126/sciadv.1600377", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://en.wikipedia.org/wiki/Dark-sky_preserve", relation="isderivedfrom", resource_type="other"),
        dict(identifier="https://www.wikidata.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.ordnancesurvey.co.uk/products/os-open-names", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.geonames.org", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com", relation="isderivedfrom", resource_type="dataset"),
        dict(identifier="https://github.com/onsvisual/uk-topojson", relation="isderivedfrom", resource_type="dataset"),
    ])
for v in json.dumps(zmeta, ensure_ascii=False):
    pass
for bad in DASH: assert bad not in json.dumps(zmeta, ensure_ascii=False), bad
json.dump(zmeta, open(os.path.join(Z, "meta.json"), "w"), indent=2, ensure_ascii=False)

rd = open(os.path.join(HERE, "readme_template.md")).read()
rd = rd.replace("/*HEADLINES*/", open(os.path.join(HERE, "readme_headlines.md")).read().strip())
rd = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", b.sub, rd)
assert "{{" not in rd
for bad in DASH: assert bad not in re.sub(r"(?m)^\|[-|]+\|$", "", rd), bad
open(os.path.join(ROOT, "README.md"), "w").write(rd)

shutil.copy(os.path.join(ROOT, "release", NAME + ".pdf"), Z)
for f in ["countries.csv", "cities.csv", "uk_areas.csv", "uk_councils.csv", "dark_sky_places.csv", "results.json"]:
    shutil.copy(os.path.join(ROOT, "data", f), Z)
zp = os.path.join(Z, "dark-skies_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ("code", "data"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn: zf.write(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), ROOT))
    for f in ("README.md", "LICENSE"): zf.write(os.path.join(ROOT, f), f)
print("release written; blog words", words)
for dp, dn, fn in os.walk(Z):
    for f in sorted(fn): print(f, os.path.getsize(os.path.join(dp, f)))
