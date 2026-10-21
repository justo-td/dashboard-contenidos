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
<title>Contenidos TodoDrones · Consumer y Agro</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,400&display=swap" rel="stylesheet">
<script src="d3.min.js"></script>
<style>
:root {
  --font-anthropic-sans: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-anthropic-serif: "Source Serif 4", Georgia, serif;
  --color-bg: #f7f6f3; --color-panel: #ffffff; --color-fg: #1f1e1c; --color-fg-muted: #6b6862;
  --color-border-line: #e4e1da; --color-ok: #1f7a4d; --color-warn: #a35a00; --color-bad: #c0392b;
  --cds-font-size-caption: 12.5px; --cds-font-size-body: 14.5px; --cds-font-size-heading: 16px; --cds-font-size-title: 26px;
  --cds-font-weight-medium: 500;
  --cds-gap-xs: 4px; --cds-gap-sm: 8px; --cds-gap-md: 16px; --cds-gap-lg: 24px; --cds-gap-xl: 40px;
  --cds-pad-xs: 4px; --cds-pad-sm: 8px; --cds-pad-md: 12px; --cds-pad-lg: 20px; --cds-radius: 10px;
  --cds-chart-muted: #d9d5cc; --cds-chart-axis: #c9c5bc; --cds-chart-grid: #ece9e2; --cds-chart-reference: #8a867e;
  --cds-surface-popover: #ffffff; --cds-border: #e4e1da; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.12);
  --cds-text-secondary: #6b6862; --cds-dur-slow: .3s;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #1b1a18; --color-panel: #252421; --color-fg: #f1efea; --color-fg-muted: #a8a49c;
    --color-border-line: #3a3834; --color-ok: #5cc28c; --color-warn: #f0a845; --color-bad: #ff7b6b;
    --cds-chart-muted: #4a4741; --cds-chart-axis: #4f4c46; --cds-chart-grid: #33312d; --cds-chart-reference: #8f8b83;
    --cds-surface-popover: #2e2d29; --cds-border: #45423d; --cds-shadow-popover: 0 4px 16px rgba(0,0,0,.5);
    --cds-text-secondary: #a8a49c;
  }
}
html, body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); }
#dash-root { max-width: 1280px; margin: 0 auto; padding: 32px 16px 48px; }
@media (min-width: 720px) { #dash-root { padding: 40px 32px 64px; } }
.dash-skeleton { color: transparent; background: var(--cds-chart-grid); border-radius: 4px; }
.site-foot { max-width: 1280px; margin: 0 auto; padding: 0 16px 32px; font-size: 12.5px; color: var(--color-fg-muted); }
@media (min-width: 720px) { .site-foot { padding: 0 32px 40px; } }
</style>
<script>
// Minimal stand-in for the Claude dashboard `dash` API, fed by data.json.
window.dash = (() => {
  const calcs = {}, cbs = [], cache = {};
  let rows = null, status = 'loading', params = {};
  const run = () => cbs.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  const api = {
    colors: ['#2f6fd0', '#d97a22', '#2a9d8f', '#8e5bd1', '#c94f7c', '#6c8a1e', '#b08900', '#5a6b7b'],
    calc(id, o) { calcs[id] = o; },
    data(id) {
      if (status !== 'ok') return { status, data: [] };
      if (id === 'cal') return { status: 'ok', data: rows };
      const c = calcs[id];
      if (!c) return { status: 'missing', data: [] };
      if (!(id in cache)) cache[id] = c.fn(...c.inputs.map((i) => api.data(i).data));
      return { status: 'ok', data: cache[id] };
    },
    onData(fn) { cbs.push(fn); fn(); },
    params() { return params; },
    setParams(p) { Object.assign(params, p); run(); },
    resetParams() { params = {}; run(); },
    setLink() {}, refresh() {},
  };
  fetch('data.json', { cache: 'no-store' })
    .then((r) => r.json())
    .then((d) => { rows = d; status = 'ok'; run(); })
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
<p class="site-foot">Datos de los calendarios de contenidos Consumer y Agro · corte __CORTE__. Se actualiza semanalmente.</p>
</body>
</html>
"""

dd = f"{corte[8:10]}/{corte[5:7]}/{corte[0:4]}" if corte else ""
open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(HEAD + page + FOOT.replace("__CORTE__", dd))
shutil.copyfile(rows_path, os.path.join(out, "data.json"))
shutil.copyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), "d3.min.js"), os.path.join(out, "d3.min.js"))
print("site ->", out)
