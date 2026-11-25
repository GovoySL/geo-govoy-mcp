# n8n · Plantillas de Geo Govoy

| Plantilla | Qué hace |
|---|---|
| [`geocodificar-google-sheets.json`](geocodificar-google-sheets.json) | **Geocodificar direcciones de Google Sheets con Geo Govoy**: lee la hoja, geocodifica por lotes de 1.000, escribe lat/lon/estado/confianza en cada fila y copia las dudosas a otra pestaña |
| [`geocode-google-sheets-en.json`](geocode-google-sheets-en.json) | La misma plantilla en inglés (nodos, notas y cabeceras `address, lat, lon, status, confidence, normalized_address, next_action, reason`; pestañas `Addresses` y `Review`). Es la versión enviada a la galería de plantillas de n8n |
| [`geocodificar-lista.json`](geocodificar-lista.json) | Geocodificar una lista fija de direcciones (ejemplo mínimo, sin Google) |

## Geocodificar direcciones de Google Sheets

```
Al ejecutar → Leer direcciones (Sheets) → Preparar lotes (Code) → Geo Govoy · geocode (HTTP)
            → Una fila por dirección (Code) → Escribir resultados (Sheets, misma fila)
                                            → ¿Dudosa? (IF) → Copiar a Dudosas (Sheets)
```

### Preparar la hoja
Pestaña **`Direcciones`** con estas cabeceras en la fila 1 (y las direcciones debajo, en texto libre):

| direccion | lat | lon | estado | confianza | direccion_normalizada | siguiente_paso | motivo |
|---|---|---|---|---|---|---|---|
| Calle Gran Vía 1, 28013 Madrid | | | | | | | |

Pestaña **`Dudosas`** con las mismas cabeceras.

### Importar y configurar
1. En n8n: **Workflows → Import from File** y elige `geocodificar-google-sheets.json` (o pega el JSON en el lienzo).
2. En los 3 nodos de Google Sheets, pega la URL de tu hoja y elige tu credencial de Google.
3. En **Geo Govoy · geocode**, crea una credencial **Header Auth**: *Name* `X-API-Key`, *Value* tu clave
   (pídela en admin@govoy.es; hay franquicia gratis cada mes). Nunca la pegues en un nodo Code ni en el JSON.
4. **Execute workflow**.

### Qué escribe
- `lat`, `lon`, `direccion_normalizada` y `confianza` (0–1) del mejor candidato.
- `estado` (`matched`, `approximate`, `review_required`, `unmatched`…) y `siguiente_paso`: `accept` (aceptar),
  `confirm` (confirmar con el cliente) o `fix` (corregir la dirección). `motivo`: avisos de la API.
- **Dudosa** = no hay candidato, `siguiente_paso` distinto de `accept` o confianza < 0,8 (cámbialo en
  `UMBRAL`, nodo *Una fila por dirección*). Se escribe igual en su fila y se copia a `Dudosas`.

### Notas
- Solo procesa filas con `lat` vacía: puedes relanzarlo o programarlo (cambia *Al ejecutar* por *Schedule Trigger*).
- Si tu columna no se llama `direccion`, cambia `COLUMNA` en *Preparar lotes*.
- 1 unidad por dirección distinta; las peticiones rechazadas no consumen. El nodo HTTP reintenta 3 veces
  (5 s) ante errores o 429.
- Solo España. Si muestras los resultados a terceros, añade la atribución: https://geo.govoy.es/fuentes

## Geocodificar una lista (ejemplo mínimo)

```
Al ejecutar → Config (tu clave) → Lista de direcciones → Geocodificar (HTTP Request) → Una fila por dirección
```

1. Importa [`geocodificar-lista.json`](geocodificar-lista.json).
2. Abre el nodo **Config** y cambia `PEGA_AQUI_TU_CLAVE` por tu clave.
   En producción, mejor una credencial **Header Auth** (`X-API-Key`) en el nodo HTTP Request en lugar del nodo Config.
3. Cambia la lista del nodo **Lista de direcciones** o sustitúyelo por tu origen (CSV, Postgres…).
   Cada elemento lleva `external_id` y `raw_address` (dirección en texto libre).
4. **Execute workflow**.

## Otros endpoints
- Hasta 1.000 direcciones por petición.
- Para tiempos entre paradas, cambia la URL a `https://geo.govoy.es/v1/matrix` con
  `{"locations":[{"lat":..,"lon":..}], "departure_time":"08:30"}`. Referencia: https://geo.govoy.es/docs
- Desde código, mejor los SDK: [`sdk/python`](../../sdk/python) (`pip install geo-govoy`) y [`sdk/js`](../../sdk/js) (`npm install geo-govoy`).
