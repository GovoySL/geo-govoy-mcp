# Make · Geocodificar direcciones de una hoja con Geo Govoy

Escenario de ejemplo: lee direcciones de Google Sheets, las geocodifica con Geo Govoy y escribe
latitud, longitud y estado en la misma hoja. Funciona con el plan gratuito de Make.

```
Google Sheets (Search Rows) → HTTP (Make a request) → Google Sheets (Update a Row)
```

## Antes de empezar
- Una clave de Geo Govoy (pídela en admin@govoy.es). No la pegues en módulos compartidos: guárdala en
  **Make → Keys** o en una variable de organización/equipo si tu plan lo permite.
- Una hoja con columnas: `id` | `direccion` | `lat` | `lon` | `estado` | `direccion_normalizada`.

## Paso a paso
1. **Crear escenario** → añade **Google Sheets › Search Rows**. Elige la hoja y filtra las filas con `lat` vacía.
   Límite: 100 filas por ejecución para empezar.
2. Añade **HTTP › Make a request**:
   - URL: `https://geo.govoy.es/v2/geocode`
   - Method: `POST`
   - Headers: `X-API-Key` = tu clave · `Content-Type` = `application/json`
   - Body type: `Raw` · Content type: `JSON (application/json)`
   - Request content:
     ```json
     {"items":[{"external_id":"{{1.id}}","raw_address":"{{1.direccion}}"}],"top_k":1}
     ```
     (`1.id` y `1.direccion` son los campos del módulo 1; selecciónalos en el panel de mapeo.)
   - **Parse response**: Sí.
3. Añade **Google Sheets › Update a Row** con Row number = `{{1.__ROW_NUMBER__}}` y:
   - `lat` = `{{2.data.results[1].candidates[1].lat}}`
   - `lon` = `{{2.data.results[1].candidates[1].lon}}`
   - `estado` = `{{2.data.results[1].status}}`
   - `direccion_normalizada` = `{{2.data.results[1].candidates[1].formatted_address}}`
   (En Make los arrays empiezan en 1.)
4. **Run once** para probar y después programa el escenario (p. ej. cada hora).

## Versión por lotes (menos operaciones de Make)
Con muchas filas, junta las direcciones con **Array aggregator** (estructura `external_id` + `raw_address`)
antes del módulo HTTP y envía hasta 1.000 en un solo `items`. Después, **Iterator** sobre `data.results` y
actualiza cada fila buscando por `external_id`.

## Otros endpoints
| Qué | URL | Cuerpo mínimo |
|---|---|---|
| Inversa | `POST /v1/reverse-geocode` | `{"items":[{"lat":40.41,"lon":-3.70}]}` |
| Matriz por hora | `POST /v1/matrix` | `{"locations":[{"lat":..,"lon":..},{"lat":..,"lon":..}],"departure_time":"08:30"}` |
| DGT en ruta | `POST /v1/traffic/route-incidents` | `{"routes":[{"stops":[{"lat":..,"lon":..,"time":"09:00"}]}]}` |
| AEMET en ruta | `POST /v1/weather/route-conditions` | `{"routes":[{"stops":[{"lat":..,"lon":..,"time":"09:00"}]}]}` |

Referencia completa: https://geo.govoy.es/docs
