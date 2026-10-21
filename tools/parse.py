"""Parse the TodoDrones content calendars (Consumer / Agro) into clean rows.

Usage: python3 parse.py <consumer_file> <agro_file> <out.json> [YYYY-MM-DD today]
Each business line is parsed and kept separate (field "linea").
"""
import csv, io, json, re, sys, unicodedata
from datetime import date

MONTHS = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,
          "agosto":8,"septiembre":9,"octubre":10,"noviembre":11,"diciembre":12}

def norm(s):
    s = (s or "").strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).lower()

def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip())

HEADER_MAP = {
    "fecha": "fecha", "plataforma": "plataforma", "formato": "formato",
    "cateogria de contenido": "categoria", "categoria de contenido": "categoria",
    "comunicacion": "comunicacion", "tematica": "tematica",
    "estado publicacion organico": "estado", "estado publicacion": "estado",
    "motivo pendiente/ no publicado": "motivo", "motivo pendiente/ no plicado": "motivo",
    "comentarios": "motivo",
    "area de desarrollo": "area", "area desarrollo": "area", "area": "area",
    "pauta": "pauta", "estado publicacion pauta": "estado_pauta",
}

def parse_date(s, year_hint):
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s or "")
    if not m: return None
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100: y += 2000
    try: return date(y, mo, d)
    except ValueError: return None

FORMATO = {"estatica":"Estática","reel":"Reel","short":"Short","shorts":"Short","video":"Video",
           "carrusel":"Carrusel","historia":"Historia","articulo":"Artículo"}
PLAT = {"instagram":"Instagram","youtube":"YouTube","linkedin":"LinkedIn","tiktok":"TikTok",
        "blog":"Blog","facebook":"Facebook"}
CAT = {"producto":"Producto","educacion":"Educación","institucional":"Institucional",
       "entretenimiento":"Entretenimiento","entretenimietno":"Entretenimiento",
       "oferta comercial":"Oferta comercial","ofertas comercial":"Oferta comercial",
       "educacin":"Educación"}

# Grouping of the free-text "Comunicación"/"Temática" into a product or theme focus, per business line.
FOCO_RULES = {
    "Consumer": [
        (r"osmo pocket", "Osmo Pocket 4 / 4P"), (r"lito", "DJI Lito X1"),
        (r"avata 360", "Avata 360"), (r"avata", "Avata 2"), (r"\bneo\b", "Neo 2"),
        (r"mini 5", "Mini 5 Pro"), (r"mavic 4", "Mavic 4 Pro"), (r"air 3", "Air 3S"),
        (r"estabiliz", "Estabilizadores"), (r"camara|osmo", "Cámaras Osmo"),
        (r"swellpro", "SwellPro"), (r"rc-n3|rc 2", "Controles RC"), (r"accesorio", "Accesorios"),
        (r"oferta|canje|bbva|financ|mayorista|drone week|preventa|entrega inmediata|envio", "Ofertas y financiación"),
        (r"asesor|primer drone|proximo|buscando|consejo|registro|tutorial|autonomia|productos|fpv", "Asesoramiento y educación"),
        (r"messi|primavera|madre|padre|mundial|argentina|lluvia|invierno", "Fechas y coyuntura"),
    ],
    "Agro": [
        (r"entrega", "Entregas a clientes"),
        (r"gira|demo|rural|curso|expo|agroactiva|visita|unsada|capacit|sorteo|^dji$|recibimos|induccion|junio", "Eventos, alianzas y capacitación"),
        (r"promo|oferta|renov|flota", "Ofertas y renovación"),
        (r"matrice", "Matrice 4T / 4TD"), (r"mavic 3|multiesp|ndvi|barbech", "Mavic 3 Multiespectral"),
        (r"t100", "Agras T100"), (r"t70|t170", "Agras T70 / T70P"), (r"t55", "Agras T55"),
        (r"estacional|nino|lluvia|gota|viento|rocio|biolog|tasa|tamano|precision|insumos", "Agronomía y estacionalidad"),
        (r"asesor|linea agras|necesita|informacion|mercader|tecnolog|servicio|agenda", "Asesoramiento, posventa y marca"),
    ],
}

def foco(linea, comunicacion, tematica):
    text = norm(comunicacion)
    for pat, label in FOCO_RULES[linea]:
        if re.search(pat, text): return label
    text = norm(comunicacion + " " + tematica)
    for pat, label in FOCO_RULES[linea]:
        if re.search(pat, text): return label
    return "Marca y entretenimiento" if linea == "Consumer" else "Otros / reposteos"

def nice(s):
    s = clean(s).rstrip(".")
    return s if s not in ("", "-", "--") else "Sin dato"

def norm_estado(s):
    n = norm(s)
    if n.startswith("publicado"): return "Publicado"
    if n.startswith("no publicado"): return "No publicado"
    if n.startswith("pendiente"): return "Pendiente"
    return ""

def parse_file(path, linea, today):
    # newline="" keeps raw line endings; a lone \r inside a cell must not split the row
    text = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n").replace("\r", " ")
    rows = []
    for block in re.split(r"^## Sheet name: ", text, flags=re.M)[1:]:
        title, _, body = block.partition("\n")
        tm = re.match(r"(\w+)\s+(\d{4})", title.strip())
        if not tm: continue
        sheet_month = MONTHS.get(norm(tm.group(1)))
        sheet_year = int(tm.group(2))
        colmap = None
        for rec in csv.reader(io.StringIO(body)):
            if not any(c.strip() for c in rec): continue
            keys = [norm(c) for c in rec]
            if "plataforma" in keys or "formato" in keys:
                if "fecha" in keys:
                    colmap = {}
                    for i, k in enumerate(keys):
                        f = HEADER_MAP.get(k)
                        if f and f not in colmap: colmap[f] = i
                continue
            if not colmap: continue
            g = lambda f: rec[colmap[f]] if f in colmap and colmap[f] < len(rec) else ""
            d = parse_date(g("fecha"), sheet_year)
            if not d: continue
            plat_raw = norm(g("plataforma"))
            if not plat_raw or "feriado" in plat_raw: continue
            # Only keep rows belonging to the sheet's month (guards against typos like 13/03 in Abril)
            fmt = FORMATO.get(norm(g("formato")), clean(g("formato")) or "Sin dato")
            cat = CAT.get(norm(g("categoria")), clean(g("categoria")) or "Sin dato")
            estado = norm_estado(g("estado"))
            if not estado:
                estado = "Programado" if d > today else "Sin registrar"
            com, tem = nice(g("comunicacion")), nice(g("tematica"))
            for p in re.split(r"\s+(?:e|y)\s+", g("plataforma").strip(), flags=re.I):
                rows.append({
                    "corte": today.isoformat(),
                    "vencido": d <= today,
                    "foco": foco(linea, com, tem),
                    "pieza": norm(com) + " | " + norm(tem),
                    "linea": linea,
                    "mes": f"{sheet_year}-{sheet_month:02d}" if sheet_month else d.strftime("%Y-%m"),
                    "fecha": d.isoformat(),
                    "semana": d.isocalendar()[1],
                    "plataforma": PLAT.get(norm(p), clean(p)),
                    "formato": fmt,
                    "categoria": cat,
                    "comunicacion": com,
                    "tematica": tem,
                    "estado": estado,
                    "motivo": clean(g("motivo")) if clean(g("motivo")) not in ("", "-", "N/A") else "",
                    "area": clean(g("area")) or "Sin dato",
                    "pauta": clean(g("pauta")),
                    "estado_pauta": clean(g("estado_pauta")),
                })
    return rows

if __name__ == "__main__":
    cons, agro, out = sys.argv[1:4]
    today = date.fromisoformat(sys.argv[4]) if len(sys.argv) > 4 else date.today()
    rows = parse_file(cons, "Consumer", today) + parse_file(agro, "Agro", today)
    json.dump({"generado": today.isoformat(), "rows": rows}, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"{len(rows)} filas -> {out}")
