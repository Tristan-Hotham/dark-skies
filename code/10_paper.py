"""Step 10. Paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_Darkest_Skies.tex
and compile it with xelatex (figures from step 8).
Run: python3 code/10_paper.py
"""
import json, os, re, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Darkest_Skies"
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "abs1": return f"{abs(v):.1f}"
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


pc = lambda v: "" if v is None else f"{v * 100:.0f}"
C = R["country"]
sel = ["CHN", "IND", "USA", "IDN", "PAK", "NGA", "BRA", "BGD", "RUS", "MEX", "JPN", "EGY", "DEU", "GBR", "FRA", "ITA", "ESP", "UKR", "IRL"]
rows = "".join(f"{tex(C[i]['name'])} & {C[i]['pop_m']:.1f} & {pc(C[i]['pop_mw'])} & {pc(C[i]['falchi_pop_mw'])} & {pc(C[i]['land_unpolluted'])}\\\\\n" for i in sel if i in C)
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{Selected countries: population (WorldPop 2023), share of people under skies that hide the Milky Way "
      "in this model and in Falchi et al. (2016, Table 2), and share of land that is not light polluted in this model (\\%).}\\label{tab:countries}"
      "\\begin{tabular}{lrrrr}\\toprule Country & People (m) & Milky Way hidden & Falchi 2016 & Land not polluted\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
N = R["uk"]["nations"]
nr = "".join(f"{n} & {pc(N[n]['pop_mw'])} & {pc(N[n]['land_mw'])} & {pc(N[n]['land_unpolluted'])} & {N[n]['land_median_mag']:.2f}\\\\\n" for n in ("England", "Scotland", "Wales", "Northern Ireland"))
nr += f"United Kingdom & {pc(R['uk']['pop_mw'])} & {pc(R['uk']['land_mw'])} & {pc(R['uk']['land_unpolluted'])} & {R['uk']['land_median_mag']:.2f}\\\\\n"
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{UK nations at 30 arc seconds: share of people and of land under skies that hide the Milky Way, "
      "share of land not light polluted (\\%), and median sky over the land (mag/arcsec\\textsuperscript{2}).}\\label{tab:nations}"
      "\\begin{tabular}{lrrrr}\\toprule Nation & People, Milky Way hidden & Land, Milky Way hidden & Land not polluted & Median sky\\\\\\midrule\n" + nr + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex")).read()
t = re.sub(r"\{\{(?!TABLE_)(.+?)\}\}", sub, t).replace("{{TABLE_COUNTRIES}}", TC).replace("{{TABLE_NATIONS}}", TN)
assert "{{" not in t and "--" not in t and "—" not in t and "–" not in t
# facts stated in words in the paper
assert R["uk_areas_darkest"][:5] == ["Na h-Eileanan Siar", "Highland", "Orkney Islands", "Shetland Islands", "Argyll and Bute"], R["uk_areas_darkest"][:5]
assert R["england_darkest"] == ["Northumberland", "Devon", "Cumbria", "Cornwall", "Dorset"], R["england_darkest"]
assert R["uk_areas_brightest"][:3] == ["Greater London", "Glasgow City", "West Midlands"]
assert [x["name"] for x in R["uk_light_fall"][:3]] == ["Tyne and Wear", "Inverclyde", "Northumberland"]
assert [x["name"] for x in R["uk_light_rise"][:2]] == ["Na h-Eileanan Siar", "Cornwall"]
assert R["uk_towns_darkest"][0]["name"] == "Hugh Town" and R["dsp_uk"][0]["name"] == "Isle of Coll" and R["dsp_uk"][-1]["name"].startswith("Moore")
assert R["uk_cities"]["London"]["mw_near"]["name"] == "Toy's Hill"
assert {c["name"] for c in R["countries_darkest"][:5]} == {"Eritrea", "Central African Rep.", "S. Sudan", "Sierra Leone", "Ethiopia"}
assert R["dsp_uk_mw_visible"] == R["dsp_uk_n"]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
if r.returncode: print(r.stdout[-3000:])
for ext in (".aux", ".log", ".out"):
    p = os.path.join(OUT, NAME + ext)
    if os.path.exists(p): os.remove(p)
shutil.copy(os.path.join(OUT, NAME + ".pdf"), os.path.join(ROOT, "release", NAME + ".pdf"))
print("paper written", r.returncode)
