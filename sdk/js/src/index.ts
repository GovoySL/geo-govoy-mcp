/**
 * Geo Govoy: cliente fino de la API REST (https://geo.govoy.es) para Node 18+, Deno, Bun y navegadores
 * de servidor. Sin dependencias: usa fetch nativo. Sin lógica de negocio.
 *
 * Docs: https://geo.govoy.es/docs · OpenAPI: https://geo.govoy.es/openapi.json
 */

export const VERSION = "0.1.0";
export const DEFAULT_BASE_URL = "https://geo.govoy.es";
export const ENV_KEY = "GEO_GOVOY_API_KEY";
export const MAX_ADDRESSES_PER_REQUEST = 1000;
export const MAX_REVERSE_POINTS_PER_REQUEST = 5000;

// ------------------------------------------------------------------ Tipos

export interface AddressInput {
  external_id?: string;
  raw_address?: string;
  street?: string;
  house_number?: string;
  unit?: string;
  postcode?: string;
  municipality?: string;
  province?: string;
  country?: string;
  query_type?: string;
  types?: string[];
}
export type Address = string | AddressInput;

export interface LatLon {
  lat: number;
  lon: number;
}
export interface Point extends LatLon {
  external_id?: string;
}
export interface Stop extends LatLon {
  id?: string;
  /** Hora local de paso, "HH:MM". */
  time?: string;
}
export interface Route {
  id?: string;
  /** AAAA-MM-DD */
  date?: string;
  stops: Stop[];
}

export interface Candidate {
  rank: number;
  entity_id: string;
  feature_type: string;
  formatted_address: string;
  street?: string | null;
  house_number?: string | null;
  postcode?: string | null;
  municipality?: string | null;
  lat: number;
  lon: number;
  source: string;
  coordinate_accuracy: string;
  confidence_score: number;
  score: number;
  match_scope: string;
  components: Record<string, unknown>;
  warnings?: string[];
  [k: string]: unknown;
}
export interface GeocodeResult {
  input: Record<string, unknown>;
  external_id?: string | null;
  query_type: string;
  input_granularity: string;
  input_quality_class: string;
  status: string;
  /** accept | confirm | fix */
  next_action: string;
  warnings?: string[];
  candidates?: Candidate[];
  [k: string]: unknown;
}
export interface BatchResponse<T> {
  request_ids: string[];
  total: number;
  results: T[];
}
export interface ReverseCandidate {
  lat: number;
  lon: number;
  distance_m: number;
  confidence: number;
  precision: string;
  address_quality?: string;
  formatted_address?: string | null;
  street?: string | null;
  house_number?: string | null;
  postcode?: string | null;
  municipality?: string | null;
  province_code?: string | null;
  source: string;
  warnings?: string[];
  [k: string]: unknown;
}
export interface ReverseResult {
  input: Point;
  external_id?: string | null;
  status: string;
  candidates: ReverseCandidate[];
  [k: string]: unknown;
}
export interface MatrixResponse {
  /** Segundos; null si no hay ruta. */
  durations: (number | null)[][];
  /** Metros; null si no hay ruta. */
  distances: (number | null)[][];
  sources: number[];
  destinations: number[];
  model: { requested: string; applied: string; name?: string | null; temporal_profile?: string | null; fallback?: boolean };
  departure_time_used: string | null;
  elements: number;
  unreachable: number;
  elapsed_ms: number;
}
export interface Quota {
  limit?: number;
  remaining?: number;
  unit?: string;
}
export type JSONObject = Record<string, any>;

export interface GeoGovoyOptions {
  /** Clave de la API. Por defecto, process.env.GEO_GOVOY_API_KEY. */
  apiKey?: string;
  baseUrl?: string;
  /** Milisegundos por petición (60 000 por defecto). */
  timeoutMs?: number;
  /** Reintentos ante 429 (respetando Retry-After) y 502/503/504. Por defecto 2. */
  maxRetries?: number;
  /** Espera máxima por reintento, en segundos (60). */
  maxRetryWaitSeconds?: number;
  /** fetch alternativo (tests, proxies). */
  fetch?: typeof fetch;
}

// ------------------------------------------------------------------ Errores

export class GeoGovoyError extends Error {
  status?: number;
  code?: string;
  requestId?: string;
  retryAfter?: number;
  body?: unknown;
  constructor(message: string, init: { status?: number; code?: string; requestId?: string; retryAfter?: number; body?: unknown } = {}) {
    super(message);
    this.name = new.target.name;
    Object.assign(this, init);
  }
}
/** 401: clave ausente o no válida. */
export class AuthenticationError extends GeoGovoyError {}
/** 403: cuenta bloqueada. */
export class PermissionDeniedError extends GeoGovoyError {}
/** 402: cuota o saldo agotados. No se reintenta. */
export class QuotaExceededError extends GeoGovoyError {}
/** 413: petición demasiado grande. */
export class PayloadTooLargeError extends GeoGovoyError {}
/** 422: el cuerpo no cumple el esquema. */
export class ValidationError extends GeoGovoyError {}
/** 429: límite por minuto o de concurrencia; mira retryAfter. */
export class RateLimitError extends GeoGovoyError {}
/** 5xx u otra respuesta inesperada. */
export class APIError extends GeoGovoyError {}
/** Error de red, DNS, TLS o timeout. */
export class ConnectionError extends GeoGovoyError {}

const BY_STATUS: Record<number, typeof GeoGovoyError> = {
  401: AuthenticationError,
  402: QuotaExceededError,
  403: PermissionDeniedError,
  413: PayloadTooLargeError,
  422: ValidationError,
  429: RateLimitError,
};
const RETRY = new Set([429, 502, 503, 504]);

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const dropUndef = (o: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && v !== null));
function chunks<T>(arr: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < arr.length; i += size) out.push(arr.slice(i, i + size));
  return out;
}
const toLatLon = (p: LatLon | [number, number]): LatLon =>
  Array.isArray(p) ? { lat: p[0], lon: p[1] } : { lat: p.lat, lon: p.lon };

function envKey(): string | undefined {
  const g = globalThis as any;
  return g.process?.env?.[ENV_KEY] ?? g.Deno?.env?.get?.(ENV_KEY);
}

// ------------------------------------------------------------------ Cliente

export class GeoGovoy {
  readonly baseUrl: string;
  timeoutMs: number;
  maxRetries: number;
  maxRetryWaitSeconds: number;
  /** Cabeceras X-Govoy-Quota-* de la última respuesta. */
  lastQuota: Quota = {};
  #key: string;
  #fetch: typeof fetch;

  constructor(options: GeoGovoyOptions = {}) {
    const key = options.apiKey ?? envKey();
    if (!key) {
      throw new GeoGovoyError(`Falta la clave: pásala en apiKey o en la variable de entorno ${ENV_KEY}. Pídela en admin@govoy.es.`);
    }
    this.#key = key;
    this.baseUrl = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeoutMs = options.timeoutMs ?? 60_000;
    this.maxRetries = options.maxRetries ?? 2;
    this.maxRetryWaitSeconds = options.maxRetryWaitSeconds ?? 60;
    const f = options.fetch ?? (globalThis as any).fetch;
    if (!f) throw new GeoGovoyError("No hay fetch nativo: usa Node 18 o superior.");
    this.#fetch = f;
  }

  /** Llamada genérica a cualquier endpoint; devuelve el JSON decodificado. */
  async request<T = any>(method: string, path: string, opts: { json?: unknown; params?: Record<string, unknown> } = {}): Promise<T> {
    let url = this.baseUrl + path;
    if (opts.params) {
      const qs = new URLSearchParams(Object.entries(dropUndef(opts.params)).map(([k, v]) => [k, String(v)])).toString();
      if (qs) url += "?" + qs;
    }
    const headers: Record<string, string> = { "X-API-Key": this.#key, Accept: "application/json" };
    if (typeof (globalThis as any).window === "undefined") headers["User-Agent"] = `geo-govoy-js/${VERSION}`;
    let body: string | undefined;
    if (opts.json !== undefined) {
      body = JSON.stringify(opts.json);
      headers["Content-Type"] = "application/json";
    }

    for (let attempt = 0; ; attempt++) {
      let res: Response;
      try {
        res = await this.#fetch(url, { method, headers, body, signal: AbortSignal.timeout(this.timeoutMs) });
      } catch (e: any) {
        throw new ConnectionError(`No se pudo conectar con ${this.baseUrl}: ${e?.cause?.code ?? e?.message ?? e}`);
      }
      this.#readQuota(res.headers);
      if (res.ok) {
        const text = await res.text();
        return (text ? JSON.parse(text) : null) as T;
      }
      const err = await GeoGovoy.#toError(res);
      if (RETRY.has(res.status) && attempt < this.maxRetries) {
        const wait = err.retryAfter ?? Math.min(2 ** attempt, 8);
        if (wait <= this.maxRetryWaitSeconds) {
          await sleep(wait * 1000);
          continue;
        }
      }
      throw err;
    }
  }

  #readQuota(h: Headers) {
    const q: Quota = {};
    const lim = h.get("X-Govoy-Quota-Limit");
    const rem = h.get("X-Govoy-Quota-Remaining");
    const unit = h.get("X-Govoy-Quota-Unit");
    if (lim && /^-?\d+$/.test(lim)) q.limit = Number(lim);
    if (rem && /^-?\d+$/.test(rem)) q.remaining = Number(rem);
    if (unit) q.unit = unit;
    if (Object.keys(q).length) this.lastQuota = q;
  }

  static async #toError(res: Response): Promise<GeoGovoyError> {
    const text = await res.text().catch(() => "");
    let body: any = text;
    try {
      body = text ? JSON.parse(text) : null;
    } catch {
      /* texto plano */
    }
    let code: string | undefined;
    let message = `HTTP ${res.status}`;
    let requestId: string | undefined;
    const detail = body && typeof body === "object" && "detail" in body ? body.detail : body;
    if (Array.isArray(detail) && detail.length) {
      code = "validation_error";
      const first = detail[0] ?? {};
      message = `${(first.loc ?? []).join(".")}: ${first.msg}`;
    } else if (detail && typeof detail === "object") {
      code = detail.error;
      message = detail.message ?? message;
      requestId = detail.request_id ?? undefined;
    } else if (typeof detail === "string" && detail) {
      message = detail;
    }
    const ra = res.headers.get("Retry-After");
    const retryAfter = ra !== null && ra !== "" && !Number.isNaN(Number(ra)) ? Number(ra) : undefined;
    const Cls = BY_STATUS[res.status] ?? APIError;
    return new Cls(message, { status: res.status, code, requestId, retryAfter, body });
  }

  // ---------------------------------------------------------------- Endpoints

  /**
   * Geocodifica direcciones de España (POST /v2/geocode). Acepta textos libres u objetos con raw_address
   * o campos sueltos. Parte en lotes de hasta 1.000 y devuelve los resultados en el mismo orden.
   * 1 unidad por dirección distinta.
   */
  async geocode(addresses: Address[], opts: { topK?: number; batchSize?: number } = {}): Promise<BatchResponse<GeocodeResult>> {
    const items = addresses.map((a) => (typeof a === "string" ? { raw_address: a } : { ...a }));
    const size = Math.max(1, Math.min(opts.batchSize ?? MAX_ADDRESSES_PER_REQUEST, MAX_ADDRESSES_PER_REQUEST));
    const out: BatchResponse<GeocodeResult> = { request_ids: [], total: 0, results: [] };
    for (const chunk of chunks(items, size)) {
      const r = await this.request("POST", "/v2/geocode", { json: { items: chunk, top_k: opts.topK ?? 1 } });
      out.request_ids.push(r.request_id);
      out.results.push(...(r.results ?? []));
    }
    out.total = out.results.length;
    return out;
  }

  /** Dirección más cercana a cada punto (POST /v1/reverse-geocode). mode: "standard" | "gps". 1 unidad por punto. */
  async reverseGeocode(
    points: (Point | [number, number])[],
    opts: { radiusM?: number; topK?: number; mode?: "standard" | "gps"; sources?: string[]; batchSize?: number } = {},
  ): Promise<BatchResponse<ReverseResult>> {
    const items = points.map((p) => (Array.isArray(p) ? { lat: p[0], lon: p[1] } : { ...p }));
    const size = Math.max(1, Math.min(opts.batchSize ?? MAX_REVERSE_POINTS_PER_REQUEST, MAX_REVERSE_POINTS_PER_REQUEST));
    const extra = dropUndef({ radius_m: opts.radiusM, top_k: opts.topK, mode: opts.mode, sources: opts.sources });
    const out: BatchResponse<ReverseResult> = { request_ids: [], total: 0, results: [] };
    for (const chunk of chunks(items, size)) {
      const r = await this.request("POST", "/v1/reverse-geocode", { json: { items: chunk, ...extra } });
      out.request_ids.push(r.request_id);
      out.results.push(...(r.results ?? []));
    }
    out.total = out.results.length;
    return out;
  }

  /**
   * Matriz de tiempos (s) y distancias (m) por carretera (POST /v1/matrix). departureTime: "08:30" o
   * "2026-12-01T08:30" (hora local). model: "govoy" (por defecto) u "osrm". Hasta 200 puntos. 1 unidad por elemento.
   */
  matrix(
    locations: (LatLon | [number, number])[],
    opts: { departureTime?: string; sources?: number[]; destinations?: number[]; model?: "govoy" | "osrm" } = {},
  ): Promise<MatrixResponse> {
    return this.request("POST", "/v1/matrix", {
      json: dropUndef({
        locations: locations.map(toLatLon),
        departure_time: opts.departureTime,
        sources: opts.sources,
        destinations: opts.destinations,
        model: opts.model,
      }),
    });
  }

  static #routes(routes: Route[] | Stop[]): Route[] {
    if (routes.length && "lat" in (routes[0] as any)) return [{ stops: routes as Stop[] }];
    return routes as Route[];
  }

  /** Incidencias DGT cerca de las paradas de una o varias rutas (POST /v1/traffic/route-incidents). 1 unidad por ruta. */
  routeTraffic(routes: Route[] | Stop[], opts: { date?: string; radiusM?: number; maxIncidents?: number } = {}): Promise<JSONObject> {
    return this.request("POST", "/v1/traffic/route-incidents", {
      json: dropUndef({ routes: GeoGovoy.#routes(routes), date: opts.date, radius_m: opts.radiusM, max_incidents: opts.maxIncidents }),
    });
  }

  /** Tiempo AEMET en cada parada a su hora y avisos (POST /v1/weather/route-conditions). 1 unidad por ruta. */
  routeWeather(routes: Route[] | Stop[], opts: { date?: string; minWarningLevel?: "yellow" | "orange" | "red" } = {}): Promise<JSONObject> {
    return this.request("POST", "/v1/weather/route-conditions", {
      json: dropUndef({ routes: GeoGovoy.#routes(routes), date: opts.date, min_warning_level: opts.minWarningLevel }),
    });
  }

  /** Previsión AEMET para un punto (GET /v1/weather/forecast). 1 unidad. */
  weatherForecast(lat: number, lon: number): Promise<JSONObject> {
    return this.request("GET", "/v1/weather/forecast", { params: { lat, lon } });
  }

  /** Avisos AEMET para un punto (GET /v1/weather/warnings). 1 unidad. */
  weatherWarnings(lat: number, lon: number, opts: { date?: string; minLevel?: "yellow" | "orange" | "red" } = {}): Promise<JSONObject> {
    return this.request("GET", "/v1/weather/warnings", { params: { lat, lon, date: opts.date, min_level: opts.minLevel } });
  }

  /** Tiempo observado entre dos fechas (GET /v1/weather/history; "to" como mucho ayer). 1 unidad. */
  weatherHistory(lat: number, lon: number, from: string, to: string): Promise<JSONObject> {
    return this.request("GET", "/v1/weather/history", { params: { lat, lon, from, to } });
  }

  /** Plan, saldo, franquicias y límites de tu cuenta (GET /v1/me). Gratis. */
  me(): Promise<JSONObject> {
    return this.request("GET", "/v1/me");
  }

  /** Consumo del mes por día, producto y canal (GET /v1/uso; mes = "AAAA-MM"). Gratis. */
  uso(mes?: string): Promise<JSONObject> {
    return this.request("GET", "/v1/uso", { params: { mes } });
  }

  /** Alias de uso(). */
  usage(mes?: string): Promise<JSONObject> {
    return this.uso(mes);
  }
}

export default GeoGovoy;
