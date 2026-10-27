"""Convert the Drive text view of a content calendar (cells unquoted, empty cells dropped)
into the '## Sheet name' + CSV export that tools/parse.py reads, for the given sheets."""
import csv, io, json, re, sys
src, out, *sheets = sys.argv[1:]
s = json.load(open(src))['contentSnippet']

def fix(t):  # undo UTF-8 read as Latin-1 (emoji), keep text that is already fine
    return re.sub(r'[\x80-\xff]+', lambda m: _dec(m.group(0)), t)
def _dec(run):
    try: return run.encode('latin-1').decode('utf-8')
    except UnicodeError: return run

ESTADOS = ('publicado', 'no publicado', 'pendiente', 'programado')
AREAS = ('cc', 'diseño', 'diseno', 'diseã±o')
DAY = r'(?:Lunes|Martes|Mi[eé]rcoles|Jueves|Viernes|S[aá]bado|Domingo)'
HDR = re.compile(r'^Fecha ,Plataforma.*?Publicacion pauta\n', re.S | re.M)
buf = io.StringIO(); w = csv.writer(buf)
stats = {}
for name in sheets:
    i = s.find('# ' + name + '\n'); j = s.find('\n# ', i + 1)
    body = s[i:j if j > 0 else None]
    body = HDR.sub('', body)
    parts = re.split(r'(?m)^(' + DAY + r')\s*\n\s*(\d{1,2}/\d{1,2}/\d{2,4}),', body)
    buf.write(f'## Sheet name: {name}\n')
    w.writerow(['Fecha', 'Plataforma', 'Formato', 'Categoria de contenido', 'Comunicacion', 'Tematica',
                'Area de desarrollo', 'Estado publicacion organico', 'Motivo Pendiente/ No publicado', 'Pauta', 'Estado Publicacion pauta'])
    n = 0
    for k in range(1, len(parts) - 2, 3):
        fecha, rec = parts[k + 1], parts[k + 2].rstrip('\n`').strip()
        f = [x.strip() for x in rec.split(',')]
        if not f or f[0].lower().startswith('feriado'): continue
        plat, fmt, cat, com, tem = (f + [''] * 5)[:5]
        idx = max((ix for ix, x in enumerate(f) if x.lower() in ESTADOS), default=None)
        estado = f[idx] if idx is not None else ''
        motivo = ''
        if idx is not None and idx + 1 < len(f) and f[idx + 1].lower() not in ('n/a', 'link', '-', ''):
            motivo = f[idx + 1]
        lim = idx if idx is not None else len(f)
        area = next((f[ix] for ix in range(lim - 1, 4, -1) if f[ix].lower() in AREAS), '')
        w.writerow([fecha, plat, fmt, cat, fix(com), fix(tem), area, estado, fix(motivo), '', ''])
        n += 1
    stats[name] = n
    buf.write('\n')
open(out, 'w', encoding='utf-8').write(buf.getvalue())
print(stats)
