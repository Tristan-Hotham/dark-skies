/* ===== charts (inline SVG) ===== */
const CLS = [["Pristine", 0], ["Near natural", 1], ["Light polluted", 2], ["Natural sky lost", 3], ["Milky Way hidden", 4], ["Never truly dark", 5]];
const CLSCOL = [0.9, 5, 30, 250, 1500, 8000].map(b => sw(b));
const goMap = (lat, lon, name) => { choose({ lat, lon, name }); };

/* countries: share of people under a Milky Way hiding sky, mine against Falchi et al. 2016 */
(() => {
  const box = document.getElementById("ctryChart"); if (!box) return;
  const rows = PD.countries.filter(c => c[2] >= 30).sort((a, b) => b[3] - a[3]);
  resp(box, (w, small) => {
    const L = small ? 112 : 170, rh = 22, H = rows.length * rh + 44, s = el("svg", { viewBox: `0 0 ${w} ${H}` }, box), x = v => L + v * (w - L - 16);
    [0, .25, .5, .75, 1].forEach(v => { el("line", { x1: x(v), x2: x(v), y1: 18, y2: H - 22, stroke: css("--rule") }, s); lbl(s, x(v), H - 6, pc(v), "lab s m", "middle"); });
    rows.forEach((c, i) => { const y = 24 + i * rh;
      const name = small && c[1].length > 14 ? c[1].slice(0, 13) + "." : c[1];
      lbl(s, L - 8, y + 11, name, "lab", "end");
      const r = el("rect", { x: x(0), y: y + 2, width: Math.max(1, x(c[3]) - x(0)), height: rh - 8, fill: css("--rose"), opacity: .85 }, s);
      if (c[4] != null) el("line", { x1: x(c[4]), x2: x(c[4]), y1: y, y2: y + rh - 4, stroke: css("--fg"), "stroke-width": 2.5 }, s);
      hover(r, `<b>${esc(c[1])}</b><br>${pc(c[3])} of ${c[2].toFixed(1)} million people under a sky that hides the Milky Way (my model, 2023)${c[4] != null ? "<br>Falchi et al. 2016: " + pc(c[4]) : ""}<br>${pc(c[5])} of land not light polluted`);
    });
    lbl(s, x(0), 12, "Share of people who cannot see the Milky Way from home", "lab s m");
  });
})();

/* UK nations: land and people by sky class */
(() => {
  const box = document.getElementById("nationChart"); if (!box) return;
  const N = PD.nations;
  resp(box, (w, small) => {
    const L = small ? 92 : 132, rh = 26, rows = []; Object.keys(N).forEach(n => { rows.push([n, "land", N[n].land]); rows.push([n, "people", N[n].pop]); });
    const per = Math.max(2, Math.floor((w - 10) / 150)), nl = Math.ceil(CLS.length / per);
    const H = rows.length * rh + 30 + nl * 20 + 24, s = el("svg", { viewBox: `0 0 ${w} ${H}` }, box), x = v => L + v * (w - L - 10);
    rows.forEach((r, i) => { const y = 8 + i * rh + (i >> 1) * 6; let acc = 0;
      lbl(s, L - 8, y + 15, r[1] === "land" ? r[0] : "people", r[1] === "land" ? "lab b" : "lab s m", "end");
      r[2].forEach((v, k) => { const rc = el("rect", { x: x(acc), y: y + 3, width: Math.max(0, x(acc + v) - x(acc)), height: rh - 8, fill: CLSCOL[k] }, s); hover(rc, `<b>${esc(r[0])}, ${r[1]}</b><br>${CLS[k][0]}: ${pc(v, 1)}`); acc += v; });
    });
    const ly0 = rows.length * rh + 30;
    CLS.forEach(([n], k) => { const lx = 10 + (k % per) * 150, ly = ly0 + Math.floor(k / per) * 20; el("rect", { x: lx, y: ly, width: 12, height: 12, fill: CLSCOL[k] }, s); lbl(s, lx + 16, ly + 10, n, "lab s"); });
  });
})();

/* county table */
(() => {
  const t = document.getElementById("areaTable"); if (!t) return;
  const cols = [["Area", 0, "s"], ["Nation", 1, "s", "wide"], ["Sky, mag", 3, "n"], ["Residents", 4, "p"], ["Land", 5, "p"], ["Change", 7, "c", "wide"]];
  let sk = 3, dir = -1;
  const draw = () => {
    const rows = PD.areas.slice().sort((a, b) => (typeof a[sk] === "string" ? a[sk].localeCompare(b[sk]) : (a[sk] ?? -1) - (b[sk] ?? -1)) * dir);
    t.innerHTML = `<thead><tr>${cols.map(c => `<th class="${c[2] !== "s" ? "num " : ""}${c[3] || ""}" data-k="${c[1]}">${c[0]}${c[1] === sk ? (dir > 0 ? " ↑" : " ↓") : ""}</th>`).join("")}</tr></thead><tbody>${rows.map(r => `<tr class="go" data-n="${esc(r[0])}">${cols.map(c => {
      const v = r[c[1]]; const f = c[2] === "n" ? v.toFixed(2) : c[2] === "p" ? pc(v) : c[2] === "c" ? (v > 0 ? "+" : "") + v.toFixed(0) + "%" : esc(v);
      return `<td class="${c[2] !== "s" ? "num " : ""}${c[3] || ""}">${c[1] === 3 ? `<span class="sw" style="background:${sw(Math.max(.6, 174 * (Math.pow(10, -0.4 * (v - 22)) - 1)))}"></span>` : ""}${f}</td>`; }).join("")}</tr>`).join("")}</tbody>`;
    t.querySelectorAll("th").forEach(th => th.onclick = () => { const k = +th.dataset.k; if (k === sk) dir = -dir; else { sk = k; dir = typeof PD.areas[0][k] === "string" ? 1 : -1; } draw(); });
    t.querySelectorAll("tr.go").forEach(tr => tr.onclick = () => { const a = PD.areaPts[tr.dataset.n]; if (a) goMap(a[0], a[1], tr.dataset.n); });
  };
  draw();
})();

/* distance from big cities to a Milky Way sky */
function distChart(id, rows, unit) {
  const box = document.getElementById(id); if (!box) return;
  resp(box, (w, small) => {
    const L = small ? 112 : 150, rh = 21, mx = Math.max(...rows.map(r => r.km)), H = rows.length * rh + 14, s = el("svg", { viewBox: `0 0 ${w} ${H}` }, box);
    const x = v => L + v / mx * (w - L - 54);
    rows.forEach((r, i) => { const y = 8 + i * rh;
      lbl(s, L - 8, y + 12, small && r.name.length > 15 ? r.name.slice(0, 14) + "." : r.name, "lab", "end");
      const rc = el("rect", { x: L, y: y + 3, width: Math.max(1, x(r.km) - L), height: rh - 8, fill: css("--night"), opacity: .82 }, s);
      lbl(s, x(r.km) + 5, y + 12, fmt(r.km) + " km", "lab s");
      hover(rc, `<b>${esc(r.name)}</b>${r.sub ? " · " + esc(r.sub) : ""}<br>${fmt(r.km)} km to the nearest place where the Milky Way should show. Click to see it on the map.`);
      rc.addEventListener("click", () => { goMap(r.lat, r.lon, r.name); });
    });
  });
}
distChart("cityChart", PD.cities.slice(0, 24).map(c => ({ name: c[0], sub: c[1] + ", " + c[2].toFixed(1) + " million", km: c[3], lat: c[5], lon: c[6] })), "Distance from the city centre (GeoNames point) to the nearest land cell below the Milky Way threshold");
distChart("ukCityChart", PD.ukcities.filter(c => c[1] === "GB" && c[3] != null).slice(0, 20).map(c => ({ name: c[0], sub: fmt(c[2] * 1000) + " people", km: c[3], lat: c[5], lon: c[6] })), "Distance from the city centre to the nearest 1 km square where the Milky Way should show");

/* change in lights seen from space, 2015 = 100 */
(() => {
  const box = document.getElementById("chgChart"); if (!box) return; const C = PD.change;
  resp(box, (w, small) => {
    const H = 260, l = 46, r = 90, t = 14, b = 30, s = el("svg", { viewBox: `0 0 ${w} ${H}` }, box);
    const ser = [["Great Britain", C.gbr, css("--night")], ["Ireland", C.irl, css("--amber")]].map(([n, v, c]) => [n, v.map(x => x / v[0] * 100), c]);
    const all = ser.flatMap(x => x[1]), lo = Math.floor(Math.min(...all) / 5) * 5, hi = Math.ceil(Math.max(...all) / 5) * 5;
    const X = i => l + i / (C.years.length - 1) * (w - l - r), Y = v => t + (hi - v) / (hi - lo) * (H - t - b);
    for (let v = lo; v <= hi; v += 5) { el("line", { x1: l, x2: w - r, y1: Y(v), y2: Y(v), stroke: v === 100 ? css("--muted") : css("--rule") }, s); lbl(s, l - 6, Y(v) + 4, v, "lab s m", "end"); }
    C.years.forEach((y, i) => { if (!small || i % 2 === 0) lbl(s, X(i), H - 8, y, "lab s m", "middle"); });
    ser.forEach(([n, v, c]) => { el("path", { d: v.map((p, i) => (i ? "L" : "M") + X(i) + " " + Y(p)).join(""), fill: "none", stroke: c, "stroke-width": 2.5 }, s);
      v.forEach((p, i) => { const d = el("circle", { cx: X(i), cy: Y(p), r: 3.5, fill: c }, s); hover(d, `<b>${n}, ${C.years[i]}</b><br>${p.toFixed(1)} (2015 = 100)`); });
      lbl(s, X(v.length - 1) + 8, Y(v[v.length - 1]) + 4, n, "lab s b"); });
  });
})();

/* model check: Globe at Night Sky Quality Meter readings against the model */
(() => {
  const box = document.getElementById("fitChart"); if (!box) return;
  resp(box, (w, small) => {
    const H = Math.min(w, 420), l = 46, b = 40, t = 10, r = 10, s = el("svg", { viewBox: `0 0 ${w} ${H}` }, box), lo = 15.5, hi = 22.2;
    const X = v => l + (v - lo) / (hi - lo) * (w - l - r), Y = v => t + (hi - v) / (hi - lo) * (H - t - b);
    for (let v = 16; v <= 22; v++) { el("line", { x1: X(v), x2: X(v), y1: t, y2: H - b, stroke: css("--rule") }, s); el("line", { x1: l, x2: w - r, y1: Y(v), y2: Y(v), stroke: css("--rule") }, s); lbl(s, X(v), H - b + 16, v, "lab s m", "middle"); lbl(s, l - 6, Y(v) + 4, v, "lab s m", "end"); }
    el("line", { x1: X(lo), y1: Y(lo), x2: X(hi), y2: Y(hi), stroke: css("--muted"), "stroke-dasharray": "4 4" }, s);
    const g = el("g", { fill: css("--violet"), "fill-opacity": .32 }, s);
    PD.fit.forEach(([o, p]) => { if (o >= lo && o <= hi && p >= lo && p <= hi) el("circle", { cx: X(o), cy: Y(p), r: 2.2 }, g); });
    lbl(s, (l + w - r) / 2, H - 6, "Measured by Globe at Night volunteers, mag/arcsec² (darker to the right)", "lab s m", "middle");
    const yl = lbl(s, 12, (t + H - b) / 2, "Model, mag/arcsec²", "lab s m", "middle"); yl.setAttribute("transform", `rotate(-90 12 ${(t + H - b) / 2})`);
  });
})();

/* Dark Sky Places in the UK */
(() => {
  const t = document.getElementById("dspTable"); if (!t) return;
  t.innerHTML = `<thead><tr><th>Place</th><th class="wide">Status</th><th class="num">Since</th><th class="num">Model sky, mag</th></tr></thead><tbody>${PD.dsp.map(d => `<tr class="go" data-la="${d[4]}" data-lo="${d[5]}" data-n="${esc(d[0])}"><td>${esc(d[0])}</td><td class="wide">${esc(d[1])}</td><td class="num">${d[2] || ""}</td><td class="num"><span class="sw" style="background:${sw(Math.max(.6, 174 * (Math.pow(10, -0.4 * (d[3] - 22)) - 1)))}"></span>${d[3].toFixed(2)}</td></tr>`).join("")}</tbody>`;
  t.querySelectorAll("tr.go").forEach(tr => tr.onclick = () => goMap(+tr.dataset.la, +tr.dataset.lo, tr.dataset.n));
})();
