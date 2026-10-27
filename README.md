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

### Si los calendarios no se pueden exportar completos

Los calendarios superan el límite de exportación de Google (xlsx/zip) y la exportación CSV trae solo la primera
hoja. En ese caso se usa la vista de texto de Drive (metadatos con el contenido completo) y se convierten los
meses que cambiaron; los meses anteriores se mantienen de `data.json`:

```
python3 tools/calendario_texto_a_csv.py <vista de texto consumer.json> /tmp/consumer.txt "Octubre 2026" "Septiembre 2026"
python3 tools/calendario_texto_a_csv.py <vista de texto agro.json> /tmp/agro.txt "Octubre 2026" "Septiembre 2026"
python3 tools/parse.py /tmp/consumer.txt /tmp/agro.txt /tmp/data_full.json <YYYY-MM-DD>
```
Validar contra la semana anterior: los meses ya cerrados tienen que coincidir fila por fila.
Las semanas con ventas sin facturación (o sin ventas cargadas) quedan como "sin dato" / "en carga", no como cero.


## Pestaña Competencia

Análisis de competencia de drones agro (relevamiento web público del 27/10/2026): Azura Drones, Alena, TDS,
Dragon Black Force, Camptech, Nico Marcucci (NFM) y Agroband frente a TodoDrones Agro.
Los datos están en `tools/competencia/*.json` (en el dashboard de Claude son los datasets `cx_*`) y
`build_site.py` los copia a `competencia/`. No cambian con la actualización semanal: para renovarlos,
reemplazar esos archivos y volver a correr `build_site.py`.

