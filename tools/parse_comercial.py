"""Parse the weekly commercial reports (Consumer comercial, Consumer e-commerce, Agro comercial).

Usage: python3 parse_comercial.py <consumer file> <agro file> <out_dir> [year]
Each input can be a Drive text export ("## Sheet name: ..." + CSV) or an .xlsx.
Writes <out_dir>/semanal.json (one row per week with data) and <out_dir>/mensual.json (month totals).
"""
import csv, io, json, os, re, sys, unicodedata
from datetime import date, timedelta

SHEETS = [  # (linea, canal, file arg index, sheet name)
    ("Consumer", "Comercial", 0, "Reporte comercial CONSUMER 2026"),
    ("Consumer", "E-commerce", 0, "Reporte ecommerce CONSUMER 2026"),
    ("Agro", "Comercial", 1, "Reporte comercial 2026 AGRO"),
]
MONTHS = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,
          "agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}

def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()

# normalized header -> field name (a repeated header gets "_2")
HEAD = {
    "gasto total": "gasto", "gasto total sin iva": "gasto", "gasto google": "gasto_google",
    "gasto meta": "gasto_meta", "gasto linkedin": "gasto_linkedin",
    "cpc meta": "cpc_meta", "cpc global": "cpc", "cpc google": "cpc_google", "cpc linkedin": "cpc_linkedin",
    "clics meta": "clics_meta", "clics google": "clics_google", "clics linkedin": "clics_linkedin",
    "clics totales": "clics", "clics total": "clics",
    "chats": "chats", "cpl chat": "cpl_chat", "% de abandono comerciales": "abandono", "% de abandono en chats": "abandono",
    "leads totales": "leads", "leads totales (sin bidcom)": "leads", "cpl lead": "cpl", "cpl lead (sin bidcom)": "cpl",
    "leads (con bidcom)": "leads_bidcom_incl",
    "provenientes de meta ads (campana wpp)": "leads_meta", "provenientes de meta ads (lead form)": "leads_form",
    "cpl meta ads (campana wpp)": "cpl_meta", "cpl meta ads (campana wpp + lead form)": "cpl_meta",
    "proveniente de otros (sitio web, linktree)": "leads_otros", "proveniente del sitio web": "leads_web",
    "cpl sitio web": "cpl_web", "leads provenientes de bidcom": "leads_bidcom",
    "leads proyecteados": "leads_proy", "leads proyectados": "leads_proy",
    "% proyectado": "leads_proy_pct", "% proyectado_2": "ventas_proy_pct", "% proyectado_3": "proy_pct_3",
    "lead rate": "lead_rate", "promedio de puntuacion de leads": "score",
    "total ventas comercial": "ventas", "total ventas comercial (solo drones)": "ventas", "ventas": "ventas",
    "ventas drones pulverizadores": "ventas_pulv", "ventas drones relevo": "ventas_relevo", "ventas accesorios": "ventas_acc",
    "cpa ventas comercial": "cpa", "cpa ventas": "cpa", "ventas pendientes de confirmar": "pendientes",
    "ventas proyectadas": "ventas_proy", "cvr real": "cvr", "cvr real (s/ leads bidcom)": "cvr", "cvr proyectado": "cvr_proy",
    "facturacion": "facturacion", "facturacion ars": "facturacion", "facturacion uds": "facturacion_usd",
    "conversion uds": "tc", "margen realizada": "margen", "margen realizado": "margen", "margen realizada ars": "margen",
    "margen en u$s": "margen_usd", "ticket promedio": "ticket", "contrib margen proyectada": "margen_obj",
    "margen promedio por unidad": "margen_unidad", "margen promedio por unidad ars": "margen_unidad", "brecha": "brecha",
    "sesiones": "sesiones", "usuarios": "usuarios", "agregados al carrito": "adc", "cpa (adc)": "cpa_adc",
    "agregados al carrito rate %": "adc_rate",
}

def load_sheet(path, name):
    if path.lower().endswith((".xlsx", ".xlsm")):
        import openpyxl, warnings
        warnings.filterwarnings("ignore")
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        ws = wb[name]
        return [list(r) for r in ws.iter_rows(values_only=True)]
    text = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n").replace("\r", " ")
    for block in re.split(r"^## Sheet name: ", text, flags=re.M)[1:]:
        title, _, body = block.partition("\n")
        if norm(title) == norm(name):
            return list(csv.reader(io.StringIO(body)))
    raise SystemExit(f"Hoja no encontrada: {name} en {path}")

def num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if not s or s.startswith("#"): return None
    pct = s.endswith("%")
    s = s.replace("$", "").replace(",", "").replace("%", "").replace(" ", "")
    try: x = float(s)
    except ValueError: return None
    return x / 100 if pct else x

def parse_range(s, month, year):
    parts = [p.strip() for p in str(s).split("-")]
    def d(p, fallback_month):
        m = re.match(r"(\d{1,2})/(\d{1,2})$", p)
        if not m: return None
        try: return date(year, int(m.group(2)), int(m.group(1)))
        except ValueError: return None
    a = d(parts[0], month) if parts else None
    b = d(parts[1], month) if len(parts) > 1 else None
    if b and month and b.month != month and (not a or a.month == month):
        b = b.replace(month=month)          # typo like "17/8 - 23/7"
    if a and b and b < a: b = b.replace(month=a.month)
    if b and not a: a = b - timedelta(days=6)  # typo like "67 - 12/7"
    if a and not b: b = a + timedelta(days=6)
    return a, b

def parse(path, name, linea, canal, year):
    rows = load_sheet(path, name)
    hi = next(i for i, r in enumerate(rows) if any(norm(c) == "mes" for c in r) and any(norm(c) == "fecha" for c in r))
    cols, seen = {}, {}
    for j, c in enumerate(rows[hi]):
        k = norm(c)
        if not k: continue
        seen[k] = seen.get(k, 0) + 1
        key = k if seen[k] == 1 else f"{k}_{seen[k]}"
        f = HEAD.get(key)
        if f and f not in cols.values(): cols[j] = f
    i_mes = next(j for j, c in enumerate(rows[hi]) if norm(c) == "mes")
    i_fecha = i_mes + 1
    weeks, months, cur = [], [], None
    for r in rows[hi + 1:]:
        r = list(r) + [None] * (len(rows[hi]) - len(r))
        mes = norm(r[i_mes]) if isinstance(r[i_mes], str) else ""
        if mes == "total":
            continue                        # yearly total
        if mes.startswith("total"):
            # the month is the one of the weeks above it (labels have typos, e.g. "TOTAL JULIO" under October)
            mnum = cur or MONTHS.get(mes.replace("total", "").strip())
            rec = {f: num(r[j]) for j, f in cols.items()}
            if mnum and rec.get("gasto") and not any(m["mes"] == f"{year}-{mnum:02d}" for m in months):
                rec.update(linea=linea, canal=canal, mes=f"{year}-{mnum:02d}", id=f"{linea}|{canal}|{year}-{mnum:02d}")
                months.append(rec)
            continue
        if mes in MONTHS: cur = MONTHS[mes]
        if cur is None or not r[i_fecha] or not re.search(r"\d", str(r[i_fecha])): continue
        a, b = parse_range(r[i_fecha], cur, year)
        if not a: continue
        rec = {f: num(r[j]) for j, f in cols.items()}
        if not rec.get("gasto"): continue   # week without data yet
        # Sales not loaded yet (no sales count, or sales without billing): money columns are
        # "sin dato", not zero, so the week does not read as a 100% drop.
        if rec.get("ventas") is None or (rec.get("ventas") and not rec.get("facturacion") and not rec.get("facturacion_usd")):
            for k in ("facturacion", "facturacion_usd", "margen", "margen_usd", "ticket", "margen_unidad"):
                if k in rec: rec[k] = None
            if rec.get("ventas") is None:
                for k in ("cpa", "cvr"):
                    if k in rec: rec[k] = None
            rec["sin_cargar"] = True
        rec.update(linea=linea, canal=canal, mes=f"{year}-{cur:02d}", semana=str(r[i_fecha]).strip(),
                   inicio=a.isoformat(), fin=b.isoformat(), id=f"{linea}|{canal}|{a.isoformat()}")
        weeks.append(rec)
    return weeks, months

if __name__ == "__main__":
    files = sys.argv[1:3]; out = sys.argv[3]; year = int(sys.argv[4]) if len(sys.argv) > 4 else 2026
    W, M = [], []
    for linea, canal, fi, name in SHEETS:
        w, m = parse(files[fi], name, linea, canal, year)
        W += w; M += m
        last = w[-1] if w else {}
        print(f"{linea} {canal}: {len(w)} semanas, última {last.get('semana')}")
    os.makedirs(out, exist_ok=True)
    json.dump(W, open(os.path.join(out, "semanal.json"), "w"), ensure_ascii=False)
    json.dump(M, open(os.path.join(out, "mensual.json"), "w"), ensure_ascii=False)
