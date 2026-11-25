// Pruebas contra la API real. Necesitan GEO_GOVOY_API_KEY; consumen unas pocas unidades.
import { test } from "node:test";
import assert from "node:assert/strict";
import { GeoGovoy, AuthenticationError, ValidationError } from "../dist/esm/index.js";

const skip = !process.env.GEO_GOVOY_API_KEY && "sin GEO_GOVOY_API_KEY";
const geo = skip ? null : new GeoGovoy();
const MADRID = { lat: 40.4193, lon: -3.6916 };
const BCN = { lat: 41.3874, lon: 2.1686 };

test("me", { skip }, async () => {
  const me = await geo.me();
  assert.equal(me.status, "activa");
  assert.ok(me.limits);
});

test("uso", { skip }, async () => {
  const u = await geo.uso();
  assert.ok(u.totales && Array.isArray(u.dias));
});

test("geocode", { skip }, async () => {
  const r = await geo.geocode(["Calle de Alcalá 50, 28014 Madrid", { external_id: "b", raw_address: "Avda. Diagonal 640, Barcelona" }]);
  assert.equal(r.total, 2);
  const c = r.results[0].candidates[0];
  assert.ok(Math.abs(c.lat - 40.419) < 0.01 && Math.abs(c.lon + 3.69) < 0.01);
  assert.equal(r.results[1].external_id, "b");
  assert.ok(geo.lastQuota.remaining !== undefined);
});

test("reverseGeocode", { skip }, async () => {
  const r = await geo.reverseGeocode([[40.4193, -3.6916]]);
  assert.equal(r.total, 1);
  assert.ok(r.results[0].candidates.length > 0);
});

test("matrix", { skip }, async () => {
  const m = await geo.matrix([MADRID, BCN], { departureTime: "08:30" });
  assert.ok(m.durations[0][1] > 3 * 3600);
  assert.ok(m.distances[0][1] > 500_000);
});

test("routeTraffic", { skip }, async () => {
  const r = await geo.routeTraffic([{ ...MADRID, time: "09:00" }, { lat: 40.45, lon: -3.69, time: "09:30" }]);
  assert.ok(Array.isArray(r.routes));
});

test("routeWeather", { skip }, async () => {
  const r = await geo.routeWeather([{ id: "r1", stops: [{ ...MADRID, time: "10:00" }] }]);
  assert.ok(Array.isArray(r.routes));
});

test("clave mala -> 401", { skip }, async () => {
  await assert.rejects(new GeoGovoy({ apiKey: "clave-que-no-existe" }).me(), (e) => e instanceof AuthenticationError && e.code === "invalid_api_key");
});

test("1.001 direcciones en una petición -> 422", { skip }, async () => {
  await assert.rejects(
    geo.request("POST", "/v2/geocode", { json: { items: Array(1001).fill({ raw_address: "x" }) } }),
    (e) => e instanceof ValidationError && e.status === 422,
  );
});
