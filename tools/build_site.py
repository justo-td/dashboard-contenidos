"""Build the standalone public site (index.html + data.json) from the dashboard page.

Usage: python3 build_site.py <dashboard index.html> <rows json> <out_dir>
The dashboard page relies on the `dash` API of the Claude dashboard; here a small
shim provides the same API (calc, data, onData, params, colors) over data.json.
"""
import json, os, shutil, sys

page_path, rows_path, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
page = open(page_path, encoding="utf-8").read()
rows = json.load(open(rows_path, encoding="utf-8"))
corte = rows[0]["corte"] if rows else ""

HEAD = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte semanal · Marketing y Comercial TodoDrones</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&display=swap" rel="stylesheet">
<script src="d3.min.js"></script>
<style>
:root { --font-anthropic-sans: "Geist", Inter, system-ui, -apple-system, "Segoe UI", sans-serif; color-scheme: light; }
html, body { margin: 0; background: #ffffff; color: #0a0a0a; font-family: var(--font-anthropic-sans); -webkit-font-smoothing: antialiased; }
#dash-root { padding: 8px clamp(16px, 3vw, 40px) 48px; }
.dash-skeleton { color: transparent; background: #f0f0f0; border-radius: 4px; }
</style>
<script>
// Minimal stand-in for the Claude dashboard `dash` API, fed by the JSON files next to this page.
window.dash = (() => {
  const calcs = {}, cbs = [], cache = {};
  const FILES = { cal: 'data.json', semanal: 'semanal.json', mensual: 'mensual.json', narrativa: 'narrativa.json' };
  const raw = {};
  let status = 'loading', params = {};
  const run = () => cbs.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  const api = {
    colors: ['#2f6fd0', '#d97a22', '#2a9d8f', '#8e5bd1', '#c94f7c', '#6c8a1e', '#b08900', '#5a6b7b'],
    calc(id, o) { calcs[id] = o; },
    data(id) {
      if (status !== 'ok') return { status, data: [] };
      if (id in FILES) return { status: 'ok', data: raw[id] || [] };
      const c = calcs[id];
      if (!c) return { status: 'missing', data: [] };
      if (!(id in cache)) cache[id] = c.fn(...c.inputs.map((i) => api.data(i).data));
      return { status: 'ok', data: cache[id] };
    },
    onData(fn) { cbs.push(fn); fn(); },
    params() { return params; },
    setParams(p) { Object.assign(params, p); run(); },
    resetParams() { params = {}; run(); },
    setLink(n) { try { history.replaceState(null, '', '#' + n); } catch (e) {} }, refresh() {},
  };
  Promise.all(Object.entries(FILES).map(([id, f]) => fetch(f, { cache: 'no-store' }).then((r) => r.json()).then((d) => { raw[id] = d; })))
    .then(() => { status = 'ok'; run(); })
    .catch(() => { status = 'error'; run(); });
  let t; window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(run, 150); });
  return api;
})();
</script>
</head>
<body>
<div id="dash-root">
"""

FOOT = """
</div>
</body>
</html>
"""

dd = f"{corte[8:10]}/{corte[5:7]}/{corte[0:4]}" if corte else ""
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(HEAD + page + FOOT.replace("__CORTE__", dd))
if os.path.abspath(rows_path) != os.path.abspath(os.path.join(out, "data.json")):
    shutil.copyfile(rows_path, os.path.join(out, "data.json"))
here = os.path.dirname(os.path.abspath(__file__))
for f in ("d3.min.js", "semanal.json", "mensual.json", "narrativa.json"):
    shutil.copyfile(os.path.join(here, f), os.path.join(out, f))
print("site ->", out)
