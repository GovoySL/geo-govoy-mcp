# n8n · Geocodificar una lista de direcciones con Geo Govoy

Workflow importable: [`geocodificar-lista.json`](geocodificar-lista.json)

```
Al ejecutar → Config (tu clave) → Lista de direcciones → Geocodificar (HTTP Request) → Una fila por dirección
```

## Cómo usarlo
1. En n8n: **Workflows → Import from File** (o copia el JSON y pégalo en el lienzo con Ctrl+V).
2. Abre el nodo **Config** y cambia `PEGA_AQUI_TU_CLAVE` por tu clave (pídela en admin@govoy.es).
   En producción, mejor una credencial **Header Auth** (`X-API-Key`) en el nodo HTTP Request en lugar del nodo Config.
3. Cambia la lista del nodo **Lista de direcciones** o sustitúyelo por tu origen (Google Sheets, CSV, Postgres…).
   Cada elemento lleva `external_id` y `raw_address` (dirección en texto libre).
4. **Execute workflow**. La salida es una fila por dirección con `estado`, `siguiente_paso` (aceptar, confirmar,
   corregir), dirección normalizada, `lat`, `lon`, confianza y precisión.

## Notas
- Hasta 1.000 direcciones por petición. Para listas mayores, pon un **Loop Over Items** en lotes de 1.000.
- 1 unidad por dirección distinta. Las peticiones rechazadas no consumen.
- Si recibes 429, añade en el nodo HTTP Request *Options → Batching* o *Retry on fail* con espera.
- Para tiempos entre paradas, cambia la URL a `https://geo.govoy.es/v1/matrix` con
  `{"locations":[{"lat":..,"lon":..}], "departure_time":"08:30"}`. Referencia: https://geo.govoy.es/docs
