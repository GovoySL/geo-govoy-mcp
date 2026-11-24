// Geo Govoy · ejemplo mínimo en JavaScript (Node 18+, fetch nativo). Solo España.
//   export GEO_API_KEY="tu_clave"     # pídela en admin@govoy.es
//   node geo_govoy.mjs
// Docs: https://geo.govoy.es/docs · OpenAPI: https://geo.govoy.es/openapi.json
// No uses la clave en código que se ejecute en el navegador: llama a Geo desde tu backend.

const BASE = "https://geo.govoy.es";
const KEY = process.env.GEO_API_KEY;
if (!KEY) throw new Error("Define GEO_API_KEY");

async function geo(path, body) {
  const res = await fetch(BASE + path, {
    method: body ? "POST" : "GET",
    headers: { "X-API-Key": KEY, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

// 1. Geocodificar con raw_address
const { results } = await geo("/v2/geocode", {
  items: [
    { external_id: "a", raw_address: "Calle de Alcalá 50, 28014 Madrid" },
    { external_id: "b", raw_address: "Gran Vía 1, Bilbao" },
  ],
});
const stops = results
  .map((r) => r.candidates?.[0])
  .filter(Boolean)
  .map((c, i) => ({ id: `p${i + 1}`, lat: c.lat, lon: c.lon }));
console.log(stops);

// 2. Inversa
console.log(await geo("/v1/reverse-geocode", { items: [{ lat: 40.4189, lon: -3.6969 }] }));

// 3. Matriz por hora de salida
const m = await geo("/v1/matrix", {
  locations: stops.map(({ lat, lon }) => ({ lat, lon })),
  departure_time: "2026-12-01T08:30",
});
console.log("segundos:", m.durations, "metros:", m.distances);

// 4. Tiempo y avisos AEMET en la ruta
console.log(await geo("/v1/weather/route-conditions", { routes: [{ id: "ruta-1", stops }] }));

// 5. Consumo (gratis)
console.log(await geo("/v1/me"));
