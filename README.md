# Dashboard de contenidos TodoDrones

Sitio estático (index.html + data.json) con las estadísticas de los calendarios de contenidos Consumer y Agro.
Se actualiza semanalmente reemplazando `data.json` (y, si cambia el diseño, `index.html`).

## Actualizar

```
python3 tools/parse.py <consumer.txt> <agro.txt> /tmp/data_full.json <YYYY-MM-DD>
python3 -c "import json;json.dump(json.load(open('/tmp/data_full.json'))['rows'],open('/tmp/rows.json','w'),ensure_ascii=False)"
python3 tools/build_site.py tools/dashboard_page.html /tmp/rows.json .
```
`tools/dashboard_page.html` es la misma página que usa el dashboard de Claude.
