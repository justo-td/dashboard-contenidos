# Dashboard de contenidos TodoDrones

Sitio estático (index.html + data.json) con las estadísticas de los calendarios de contenidos Consumer y Agro.
Se actualiza semanalmente reemplazando `data.json` (y, si cambia el diseño, `index.html`).

## Actualizar

```
python3 tools/parse.py <consumer.txt> <agro.txt> /tmp/data_full.json <YYYY-MM-DD>
python3 -c "import json;json.dump(json.load(open('/tmp/data_full.json'))['rows'],open('/tmp/rows.json','w'),ensure_ascii=False)"
python3 tools/parse_comercial.py <consumer proceso comercial> <agro proceso comercial .xlsx> tools/
# escribir el análisis de la semana en tools/narrativa.json
python3 tools/build_site.py tools/dashboard_page.html /tmp/rows.json .
```
`tools/dashboard_page.html` es la misma página que usa el dashboard de Claude.

## Pestaña Competencia

Análisis de competencia de drones agro (relevamiento web público del 27/10/2026): Azura Drones, Alena, TDS,
Dragon Black Force, Camptech, Nico Marcucci (NFM) y Agroband frente a TodoDrones Agro.
Los datos están en `tools/competencia/*.json` (en el dashboard de Claude son los datasets `cx_*`) y
`build_site.py` los copia a `competencia/`. No cambian con la actualización semanal: para renovarlos,
reemplazar esos archivos y volver a correr `build_site.py`.

