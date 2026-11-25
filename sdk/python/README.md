# geo-govoy (Python)

Cliente oficial y mínimo de la API REST de **[Geo Govoy](https://geo.govoy.es)**: datos de calle y carretera para
planificar rutas de reparto en **España**. Geocodificación por lotes, geocodificación inversa, matriz de tiempos
según la hora de salida, incidencias DGT y tiempo AEMET en ruta, y consumo de tu cuenta.

[English below](#english) · [Referencia de la API](https://geo.govoy.es/docs) · [OpenAPI](https://geo.govoy.es/openapi.json) · Licencia MIT

## Español

### Instalación

```bash
pip install geo-govoy
```

Python 3.9 o superior. Sin dependencias salvo `certifi` (certificados TLS).

### Clave

Pide tu clave en **admin@govoy.es** (hay franquicia gratis cada mes) y guárdala en una variable de entorno:

```bash
export GEO_GOVOY_API_KEY="tu_clave"        # PowerShell: $env:GEO_GOVOY_API_KEY="tu_clave"
```

No la escribas en el código ni la subas a un repositorio.

### Ejemplos

```python
from geo_govoy import GeoGovoy, QuotaExceededError

geo = GeoGovoy()  # lee GEO_GOVOY_API_KEY

# 1. Geocodificar (textos libres o campos sueltos; parte en lotes de 1.000 automáticamente)
r = geo.geocode([
    "Calle de Alcalá 50, 28014 Madrid",
    {"external_id": "pedido-2", "raw_address": "Avda. Diagonal 640, Barcelona"},
])
for res in r["results"]:
    c = (res.get("candidates") or [None])[0]
    print(res["external_id"], res["status"], res["next_action"],
          c and (c["lat"], c["lon"], c["confidence_score"]))
# next_action: accept (aceptar), confirm (confirmar con el cliente) o fix (corregir)

# 2. Geocodificación inversa
geo.reverse_geocode([(40.4193, -3.6916), {"lat": 41.3874, "lon": 2.1686, "external_id": "p2"}])

# 3. Matriz de tiempos (segundos) y distancias (metros) saliendo a las 08:30
m = geo.matrix([(40.4193, -3.6916), (40.45, -3.69), (40.38, -3.72)], departure_time="08:30")
print(m["durations"])

# 4. Incidencias DGT y tiempo AEMET en las paradas de una ruta, a su hora de paso
paradas = [{"lat": 40.4193, "lon": -3.6916, "time": "09:00"}, {"lat": 40.45, "lon": -3.69, "time": "09:40"}]
geo.route_traffic(paradas)                       # una ruta como lista de paradas
geo.route_weather([{"id": "ruta-1", "stops": paradas}], min_warning_level="orange")

# 5. Cuenta y consumo (gratis)
geo.me()             # plan, cuotas, límites
geo.uso("2026-11")   # consumo por día, producto y canal
print(geo.last_quota)  # cabeceras X-Govoy-Quota-* de la última respuesta
```

También: `weather_forecast(lat, lon)`, `weather_warnings(lat, lon)`, `weather_history(lat, lon, "2026-11-01", "2026-11-20")`
y `request(method, path, json_body=..., params=...)` para cualquier otro endpoint.

### Errores y reintentos

| HTTP | Excepción | Qué hace el cliente |
|---|---|---|
| 401 | `AuthenticationError` | Nada: revisa la clave |
| 402 | `QuotaExceededError` | Nada: cuota o saldo del mes agotados |
| 403 | `PermissionDeniedError` | Nada: cuenta bloqueada |
| 413 | `PayloadTooLargeError` | Nada: usa lotes más pequeños (`batch_size`) |
| 422 | `ValidationError` | Nada: el cuerpo no cumple el esquema |
| 429 | `RateLimitError` | Reintenta hasta `max_retries` (2) esperando `Retry-After` |
| 502/503/504 | `APIError` | Reintenta con espera exponencial |
| red/TLS | `ConnectionError` | Nada |

Todas heredan de `GeoGovoyError` y llevan `status`, `code` (p. ej. `quota_exceeded`), `message`, `request_id`,
`retry_after` y `body`. Las peticiones rechazadas no consumen unidades.

```python
geo = GeoGovoy(timeout=30, max_retries=4, max_retry_wait=90)
```

### Tests

```bash
pip install -e ".[test]"
pytest tests/test_errors_mock.py            # sin red
GEO_GOVOY_API_KEY=... pytest tests/         # también contra la API real (gasta unas pocas unidades)
```

### Datos y atribución

Si muestras resultados a terceros, incluye la atribución de las fuentes: https://geo.govoy.es/fuentes.
Solo España. Términos: https://geo.govoy.es/terminos.

---

## English

Official, minimal client for the **[Geo Govoy](https://geo.govoy.es)** REST API: street and road data to plan
delivery routes in **Spain**. Batch geocoding, reverse geocoding, departure-time-aware travel-time matrices,
DGT traffic incidents and AEMET weather along a route, and account usage.

### Install

```bash
pip install geo-govoy
```

Python 3.9+. Only dependency: `certifi`.

### Key

Ask for a key at **admin@govoy.es** (free monthly allowance) and set `GEO_GOVOY_API_KEY`. Never hard-code it.

### Usage

```python
from geo_govoy import GeoGovoy

geo = GeoGovoy()  # reads GEO_GOVOY_API_KEY

r = geo.geocode(["Calle de Alcalá 50, 28014 Madrid"])        # auto-batches in chunks of 1,000
geo.reverse_geocode([(40.4193, -3.6916)])
geo.matrix([(40.4193, -3.6916), (41.3874, 2.1686)], departure_time="08:30")  # seconds / meters
geo.route_traffic([{"lat": 40.4193, "lon": -3.6916, "time": "09:00"}])     # DGT incidents
geo.route_weather([{"lat": 40.4193, "lon": -3.6916, "time": "09:00"}])     # AEMET weather + warnings
geo.me(); geo.uso()                                                         # account and usage (free)
```

Errors map to exceptions (`AuthenticationError` 401, `QuotaExceededError` 402, `PayloadTooLargeError` 413,
`ValidationError` 422, `RateLimitError` 429…), all subclasses of `GeoGovoyError`. 429 and 502/503/504 are retried
(`max_retries=2`), honouring `Retry-After`.

MIT licensed. © GOVOY SOLUTIONS SL.
