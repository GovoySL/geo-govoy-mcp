# Ejemplos · Geo Govoy API

Ejemplos mínimos de la API REST de [Geo Govoy](https://geo.govoy.es) (datos de calle y carretera para rutas
de reparto en **España**). Todos leen la clave de la variable de entorno `GEO_API_KEY` y la envían en la
cabecera `X-API-Key` (también vale `Authorization: Bearer <clave>`).

| Archivo | Qué hace |
|---|---|
| [`curl.sh`](curl.sh) | Cuenta, geocodificación (`raw_address`), inversa, matriz por hora de salida, DGT, AEMET |
| [`python/geo_govoy.py`](python/geo_govoy.py) | Geocodifica una lista, matriz a las 08:30, incidencias DGT y consumo (`requests`) |
| [`javascript/geo_govoy.mjs`](javascript/geo_govoy.mjs) | Lo mismo en Node 18+ con `fetch` |

Más:
- Colección de Postman: [`integrations/postman/`](../integrations/postman/)
- n8n, Make y Claude Code: [`integrations/`](../integrations/)
- Referencia completa: [geo.govoy.es/docs](https://geo.govoy.es/docs) · OpenAPI: [`/openapi.json`](https://geo.govoy.es/openapi.json)

## Clave
Escribe a **admin@govoy.es** (asunto «Clave de la API de GOVOY") desde el correo de tu empresa. Hay franquicia
gratis cada mes; precios en [govoy.es/geo/precios](https://govoy.es/geo/precios/). Trata la clave como una
contraseña: nunca en una URL, en código publicado ni en JavaScript del navegador.

## Errores habituales
| Código | Significado |
|---|---|
| 401 `invalid_api_key` | Falta la clave o no es válida |
| 402 `quota_exceeded` | Cuota del mes agotada (cabeceras `X-Govoy-Quota-*`) |
| 429 `rate_limit` | Demasiadas peticiones por minuto: respeta `Retry-After` |
| 422 | El cuerpo no cumple el esquema (mira `/docs`) |

Las peticiones rechazadas no consumen unidades.
