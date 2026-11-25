// Manejo de errores y reintentos con un fetch simulado (sin red ni clave).
import { test } from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { GeoGovoy, AuthenticationError, QuotaExceededError, PayloadTooLargeError, RateLimitError, GeoGovoyError } from "../dist/esm/index.js";

const json = (status, body, headers = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });

function client(handler) {
  const calls = [];
  const fetch = async (url, init) => {
    calls.push({ url, init });
    return handler(new URL(url), init, calls.length);
  };
  return { geo: new GeoGovoy({ apiKey: "test", baseUrl: "http://mock", fetch }), calls };
}

test("CJS y ESM exportan lo mismo", () => {
  const require = createRequire(import.meta.url);
  const cjs = require("../dist/cjs/index.js");
  assert.equal(typeof cjs.GeoGovoy, "function");
  assert.equal(cjs.VERSION, "0.1.0");
});

test("sin clave lanza error", () => {
  const prev = process.env.GEO_GOVOY_API_KEY;
  delete process.env.GEO_GOVOY_API_KEY;
  try {
    assert.throws(() => new GeoGovoy(), GeoGovoyError);
  } finally {
    if (prev !== undefined) process.env.GEO_GOVOY_API_KEY = prev;
  }
});

test("401 -> AuthenticationError con code", async () => {
  const { geo } = client(() => json(401, { detail: { error: "invalid_api_key", message: "API key invalida o ausente." } }));
  await assert.rejects(geo.me(), (e) => e instanceof AuthenticationError && e.status === 401 && e.code === "invalid_api_key");
});

test("402 no se reintenta", async () => {
  const { geo, calls } = client(() => json(402, { detail: { error: "quota_exceeded", message: "Cuota agotada" } }));
  await assert.rejects(geo.me(), QuotaExceededError);
  assert.equal(calls.length, 1);
});

test("413 -> PayloadTooLargeError", async () => {
  const { geo } = client(() => json(413, { detail: { error: "payload_too_large", message: "Demasiado grande" } }));
  await assert.rejects(geo.geocode(["x"]), PayloadTooLargeError);
});

test("429 respeta Retry-After y luego responde", async () => {
  const { geo, calls } = client((u, i, n) =>
    n === 1
      ? json(429, { detail: { error: "rate_limit", message: "Espera" } }, { "Retry-After": "1" })
      : json(200, { ok: true }, { "X-Govoy-Quota-Limit": "100", "X-Govoy-Quota-Remaining": "41", "X-Govoy-Quota-Unit": "units" }),
  );
  const t0 = Date.now();
  assert.deepEqual(await geo.me(), { ok: true });
  assert.ok(Date.now() - t0 >= 900);
  assert.equal(calls.length, 2);
  assert.deepEqual(geo.lastQuota, { limit: 100, remaining: 41, unit: "units" });
});

test("429 se rinde tras maxRetries", async () => {
  const { geo, calls } = client(() => json(429, { detail: { error: "rate_limit", message: "Espera" } }, { "Retry-After": "0" }));
  await assert.rejects(geo.me(), (e) => e instanceof RateLimitError && e.retryAfter === 0);
  assert.equal(calls.length, 3);
});

test("geocode parte en lotes y mantiene el orden", async () => {
  const { geo, calls } = client((u, init, n) => {
    const { items } = JSON.parse(init.body);
    return json(200, { request_id: `r${n}`, results: items.map((it) => ({ external_id: it.external_id, status: "matched" })) });
  });
  const r = await geo.geocode(
    Array.from({ length: 25 }, (_, i) => ({ external_id: String(i), raw_address: `Calle ${i}` })),
    { batchSize: 10 },
  );
  assert.equal(calls.length, 3);
  assert.equal(r.total, 25);
  assert.deepEqual(r.results.map((x) => x.external_id), Array.from({ length: 25 }, (_, i) => String(i)));
  assert.equal(calls[0].init.headers["X-API-Key"], "test");
});
