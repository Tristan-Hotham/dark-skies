"""Step 7. Build index.html from code/page_template.html and code/page_text.html. Every number in the text is a
{{path|format}} token filled from data/results.json; the page tables (work/page_data.json) are embedded; grids and
search lists load from data/page/.
Run: python3 code/07_build_site.py
"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
PD = json.load(open(os.path.join(ROOT, "work", "page_data.json"), encoding="utf-8"))


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "abs1": return f"{abs(v):.1f}"
    raise ValueError(f)


def sub(m):
    return fmt(get(m.group(1).strip()), m.group(3))


# facts stated in words in the page text
assert R["uk_areas_darkest"][:5] == ["Na h-Eileanan Siar", "Highland", "Orkney Islands", "Shetland Islands", "Argyll and Bute"]
assert R["england_darkest"] == ["Northumberland", "Devon", "Cumbria", "Cornwall", "Dorset"]
assert [x["name"] for x in R["uk_light_fall"][:3]] == ["Tyne and Wear", "Inverclyde", "Northumberland"]
assert [x["name"] for x in R["uk_light_rise"][:2]] == ["Na h-Eileanan Siar", "Cornwall"]
assert [t["name"] for t in R["uk_towns_darkest"][:5]] == ["Hugh Town", "New Galloway", "Tobermory", "Chagford", "Whithorn"]
assert R["dsp_uk"][0]["name"] == "Isle of Coll" and R["dsp_uk"][1]["name"].startswith("Tomintoul") and R["dsp_uk"][-1]["name"].startswith("Moore")
assert R["uk_cities"]["London"]["mw_near"]["name"] == "Toy's Hill" and R["uk_cities"]["Manchester"]["mw_near"]["name"] == "Padfield"
assert {c["name"] for c in R["countries_darkest"][:5]} == {"Eritrea", "Central African Rep.", "S. Sudan", "Sierra Leone", "Ethiopia"}
assert {c["iso3"] for c in R["countries_brightest"][:8]} == {"HKG", "SGP", "PSE", "BHR", "QAT", "KWT", "ISR", "EGY"}
assert R["dsp_uk_mw_visible"] == R["dsp_uk_n"] and R["countries_no_lights"] == ["Kosovo"]
assert R["country"]["UKR"]["pop_mw"] < R["country"]["UKR"]["falchi_pop_mw"] - .05

TOK = re.compile(r"\{\{([^}|]+)(\|(\w+))?\}\}")

if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    txt = open(os.path.join(HERE, "page_text.html"), encoding="utf-8").read()
    parts = dict(re.findall(r"<!--@(\w+)-->(.*?)<!--@end-->", txt, flags=re.S))
    for k in ("INTRO", "BODY"):
        tpl = tpl.replace(f"/*{k}*/", parts[k].strip())
    tpl = tpl.replace("/*CHARTS*/", open(os.path.join(HERE, "page_charts.js"), encoding="utf-8").read())
    html = TOK.sub(sub, tpl)
    html = html.replace("/*RESULTS*/", json.dumps({"meta": R["meta"]}, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*PD*/", json.dumps(PD, ensure_ascii=False, separators=(",", ":")))
    assert "{{" not in html
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
