# geo-govoy (JavaScript / TypeScript)

Cliente oficial y mínimo de la API REST de **[Geo Govoy](https://geo.govoy.es)**: datos de calle y carretera para
planificar rutas de reparto en **España**. Geocodificación por lotes, geocodificación inversa, matriz de tiempos
según la hora de salida, incidencias DGT y tiempo AEMET en ruta, y consumo de tu cuenta.

Sin dependencias (fetch nativo) · ESM y CommonJS · tipos incluidos · Node 18.17+, Bun y Deno · Licencia MIT

[English below](#english) · [Referencia de la API](https://geo.govoy.es/docs) · [OpenAPI](https://geo.govoy.es/openapi.json)

## Español

### Instalación

```bash
npm install geo-govoy
```

### Clave

Pide tu clave en **admin@govoy.es** (hay franquicia gratis cada mes) y guárdala en `GEO_GOVOY_API_KEY`.
Úsala solo en el servidor: nunca en código que se ejecute en el navegador ni en un repositorio.

### Ejemplos

```ts
import { GeoGovoy, QuotaExceededError } from "geo-govoy";   // o: const { GeoGovoy } = require("geo-govoy");

const geo = new GeoGovoy(); // lee GEO_GOVOY_API_KEY

// 1. Geocodificar (textos libres u objetos; parte en lotes de 1.000 automáticamente)
const r = await geo.geocode([
  "Calle de Alcalá 50, 28014 Madrid",
  { external_id: "pedido-2", raw_address: "Avda. Diagonal 640, Barcelona" },
]);
for (const res of r.results) {
  const c = res.candidates?.[0];
  console.log(res.external_id, res.status, res.next_action, c?.lat, c?.lon, c?.confidence_score);
}
// next_action: accept (aceptar), confirm (confirmar con el cliente) o fix (corregir)

// 2. Geocodificación inversa
await geo.reverseGeocode([[40.4193, -3.6916], { lat: 41.3874, lon: 2.1686, external_id: "p2" }]);

// 3. Matriz de tiempos (s) y distancias (m) saliendo a las 08:30
const m = await geo.matrix([[40.4193, -3.6916], [40.45, -3.69]], { departureTime: "08:30" });

// 4. DGT y AEMET en las paradas de una ruta, a su hora de paso
const paradas = [{ lat: 40.4193, lon: -3.6916, time: "09:00" }, { lat: 40.45, lon: -3.69, time: "09:40" }];
await geo.routeTraffic(paradas);
await geo.routeWeather([{ id: "ruta-1", stops: paradas }], { minWarningLevel: "orange" });

// 5. Cuenta y consumo (gratis)
await geo.me();
await geo.uso("2026-11");
console.log(geo.lastQuota); // cabeceras X-Govoy-Quota-* de la última respuesta
```

También: `weatherForecast(lat, lon)`, `weatherWarnings(lat, lon)`, `weatherHistory(lat, lon, from, to)` y
`request(method, path, { json, params })` para cualquier otro endpoint.

### Errores y reintentos

| HTTP | Error | Qué hace el cliente |
|---|---|---|
| 401 | `AuthenticationError` | Nada: revisa la clave |
| 402 | `QuotaExceededError` | Nada: cuota o saldo agotados |
| 403 | `PermissionDeniedError` | Nada: cuenta bloqueada |
| 413 | `PayloadTooLargeError` | Nada: lotes más pequeños (`batchSize`) |
| 422 | `ValidationError` | Nada: el cuerpo no cumple el esquema |
| 429 | `RateLimitError` | Reintenta hasta `maxRetries` (2) esperando `Retry-After` |
| 502/503/504 | `APIError` | Reintenta con espera exponencial |
| red/TLS/timeout | `ConnectionError` | Nada |

Todos heredan de `GeoGovoyError` y llevan `status`, `code`, `message`, `requestId`, `retryAfter` y `body`.

```ts
const geo = new GeoGovoy({ timeoutMs: 30_000, maxRetries: 4 });
```

### Tests

```bash
npm install && npm test        # sin clave solo corren los tests simulados
GEO_GOVOY_API_KEY=... npm test # también contra la API real (gasta unas pocas unidades)
```

Si muestras resultados a terceros, incluye la atribución: https://geo.govoy.es/fuentes. Solo España.

---

## English

Official, minimal, zero-dependency client for the **[Geo Govoy](https://geo.govoy.es)** REST API (Spain only):
batch geocoding, reverse geocoding, departure-time-aware travel-time matrices, DGT traffic incidents and AEMET
weather along a route, and account usage. ESM + CJS, typed, native `fetch`.

```bash
npm install geo-govoy
```

```ts
import { GeoGovoy } from "geo-govoy";
const geo = new GeoGovoy(); // reads GEO_GOVOY_API_KEY (ask at admin@govoy.es)

await geo.geocode(["Calle de Alcalá 50, 28014 Madrid"]);            // auto-batches in chunks of 1,000
await geo.reverseGeocode([[40.4193, -3.6916]]);
await geo.matrix([[40.4193, -3.6916], [41.3874, 2.1686]], { departureTime: "08:30" });
await geo.routeTraffic([{ lat: 40.4193, lon: -3.6916, time: "09:00" }]);
await geo.routeWeather([{ lat: 40.4193, lon: -3.6916, time: "09:00" }]);
await geo.me(); await geo.uso();
```

HTTP errors become typed errors (`AuthenticationError`, `QuotaExceededError`, `PayloadTooLargeError`,
`ValidationError`, `RateLimitError`…). 429 and 502/503/504 are retried, honouring `Retry-After`. Server-side only:
never ship your key to a browser.

MIT licensed. © GOVOY SOLUTIONS SL.
