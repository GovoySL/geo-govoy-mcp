"""Cliente fino de la API REST de Geo Govoy (https://geo.govoy.es).

Sin lógica de negocio: cada método es una llamada (o varias, si hay que partir en lotes) a un endpoint.
"""
from __future__ import annotations

import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union

from . import __version__
from .errors import ConnectionError, GeoGovoyError, error_for
from .types import (
    JSON,
    Account,
    Address,
    GeocodeResponse,
    MatrixResponse,
    Point,
    Quota,
    ReverseResponse,
    Route,
    Stop,
    Usage,
)

DEFAULT_BASE_URL = "https://geo.govoy.es"
ENV_KEY = "GEO_GOVOY_API_KEY"
MAX_ADDRESSES_PER_REQUEST = 1000
MAX_REVERSE_POINTS_PER_REQUEST = 5000
_RETRY_STATUSES = {429, 502, 503, 504}


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover
        return ssl.create_default_context()


def _chunks(seq: Sequence[Any], size: int) -> Iterable[Sequence[Any]]:
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def _drop_none(d: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class GeoGovoy:
    """Cliente de Geo Govoy.

    >>> from geo_govoy import GeoGovoy
    >>> geo = GeoGovoy()  # lee la clave de GEO_GOVOY_API_KEY
    >>> geo.geocode(["Calle de Alcalá 50, 28014 Madrid"])["results"][0]["candidates"][0]["lat"]

    :param api_key: clave de la API. Por defecto, la variable de entorno ``GEO_GOVOY_API_KEY``.
    :param base_url: por defecto ``https://geo.govoy.es``.
    :param timeout: segundos por petición.
    :param max_retries: reintentos ante 429 (respetando ``Retry-After``) y 502/503/504.
    :param max_retry_wait: espera máxima por reintento, en segundos.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = 2,
        max_retry_wait: float = 60.0,
        ssl_context: Optional[ssl.SSLContext] = None,
    ) -> None:
        key = api_key or os.environ.get(ENV_KEY)
        if not key:
            raise GeoGovoyError(
                f"Falta la clave: pásala como api_key o en la variable de entorno {ENV_KEY}. "
                "Pídela en admin@govoy.es."
            )
        self._key = key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_retry_wait = max_retry_wait
        self._ctx = ssl_context or _ssl_context()
        self.last_quota: Quota = {}
        """Cabeceras X-Govoy-Quota-* de la última respuesta (limit, remaining, unit)."""

    def __repr__(self) -> str:
        return f"GeoGovoy(base_url={self.base_url!r})"

    # ------------------------------------------------------------------ HTTP

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Mapping[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Llamada genérica a cualquier endpoint. Devuelve el JSON decodificado."""
        url = self.base_url + path
        if params:
            clean = _drop_none(params)
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        data = None
        headers = {
            "X-API-Key": self._key,
            "Accept": "application/json",
            "User-Agent": f"geo-govoy-python/{__version__}",
        }
        if json_body is not None:
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        attempt = 0
        while True:
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                    self._read_quota(resp.headers)
                    raw = resp.read()
                    return json.loads(raw) if raw else None
            except urllib.error.HTTPError as e:
                self._read_quota(e.headers)
                err = self._to_error(e)
                if e.code in _RETRY_STATUSES and attempt < self.max_retries:
                    wait = err.retry_after if err.retry_after is not None else min(2 ** attempt, 8)
                    if wait <= self.max_retry_wait:
                        time.sleep(wait)
                        attempt += 1
                        continue
                raise err from None
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                raise ConnectionError(f"No se pudo conectar con {self.base_url}: {e}") from e

    def _read_quota(self, headers: Any) -> None:
        if headers is None:
            return
        q: Quota = {}
        for name, key in (("X-Govoy-Quota-Limit", "limit"), ("X-Govoy-Quota-Remaining", "remaining")):
            v = headers.get(name)
            if v is not None and v.lstrip("-").isdigit():
                q[key] = int(v)  # type: ignore[literal-required]
        unit = headers.get("X-Govoy-Quota-Unit")
        if unit:
            q["unit"] = unit
        if q:
            self.last_quota = q

    @staticmethod
    def _to_error(e: urllib.error.HTTPError) -> GeoGovoyError:
        raw = b""
        try:
            raw = e.read()
        except Exception:  # pragma: no cover
            pass
        body: Any = None
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = raw.decode("utf-8", "replace")
        code = None
        message = f"HTTP {e.code}"
        request_id = None
        detail = body.get("detail", body) if isinstance(body, dict) else body
        if isinstance(detail, dict):
            code = detail.get("error")
            message = detail.get("message") or message
            request_id = detail.get("request_id")
        elif isinstance(detail, list) and detail:  # 422 de validación
            code = "validation_error"
            first = detail[0]
            if isinstance(first, dict):
                loc = ".".join(str(x) for x in first.get("loc", []))
                message = f"{loc}: {first.get('msg')}"
        elif isinstance(detail, str):
            message = detail
        retry_after = None
        ra = e.headers.get("Retry-After") if e.headers is not None else None
        if ra:
            try:
                retry_after = float(ra)
            except ValueError:
                retry_after = None
        cls = error_for(e.code)
        return cls(message, status=e.code, code=code, request_id=request_id, retry_after=retry_after, body=body)

    # ------------------------------------------------------------ Endpoints

    def geocode(
        self,
        addresses: Sequence[Address],
        *,
        top_k: int = 1,
        batch_size: int = MAX_ADDRESSES_PER_REQUEST,
    ) -> GeocodeResponse:
        """Geocodifica direcciones de España (``POST /v2/geocode``).

        Acepta textos libres (``"Calle Mayor 1, Madrid"``) o diccionarios con ``raw_address`` o campos
        sueltos (``street``, ``house_number``, ``postcode``, ``municipality``…) y ``external_id``.
        Parte la lista en lotes de ``batch_size`` (máx. 1.000) y devuelve los resultados en el mismo orden.
        1 unidad por dirección distinta.
        """
        items: List[Dict[str, Any]] = [
            {"raw_address": a} if isinstance(a, str) else dict(a) for a in addresses
        ]
        batch_size = max(1, min(batch_size, MAX_ADDRESSES_PER_REQUEST))
        out: GeocodeResponse = {"request_ids": [], "total": 0, "results": []}
        for chunk in _chunks(items, batch_size):
            r = self.request("POST", "/v2/geocode", json_body={"items": list(chunk), "top_k": top_k})
            out["request_ids"].append(r.get("request_id"))
            out["results"].extend(r.get("results", []))
        out["total"] = len(out["results"])
        return out

    def reverse_geocode(
        self,
        points: Sequence[Point],
        *,
        radius_m: Optional[int] = None,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
        sources: Optional[List[str]] = None,
        batch_size: int = MAX_REVERSE_POINTS_PER_REQUEST,
    ) -> ReverseResponse:
        """Dirección más cercana a cada punto (``POST /v1/reverse-geocode``). ``mode``: ``standard`` o ``gps``.

        Acepta diccionarios ``{"lat", "lon", "external_id"?}`` o tuplas ``(lat, lon)``. 1 unidad por punto.
        """
        items = [p if isinstance(p, Mapping) else {"lat": p[0], "lon": p[1]} for p in points]  # type: ignore[index]
        batch_size = max(1, min(batch_size, MAX_REVERSE_POINTS_PER_REQUEST))
        extra = _drop_none({"radius_m": radius_m, "top_k": top_k, "mode": mode, "sources": sources})
        out: ReverseResponse = {"request_ids": [], "total": 0, "results": []}
        for chunk in _chunks(items, batch_size):
            r = self.request("POST", "/v1/reverse-geocode", json_body={"items": list(chunk), **extra})
            out["request_ids"].append(r.get("request_id"))
            out["results"].extend(r.get("results", []))
        out["total"] = len(out["results"])
        return out

    def matrix(
        self,
        locations: Sequence[Union[Point, Sequence[float]]],
        *,
        departure_time: Optional[str] = None,
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None,
        model: Optional[str] = None,
    ) -> MatrixResponse:
        """Matriz de tiempos (s) y distancias (m) por carretera (``POST /v1/matrix``).

        ``departure_time``: ``"08:30"`` o ``"2026-12-01T08:30"`` (hora local). ``model``: ``govoy`` (por defecto,
        modelo de conducción de Govoy) u ``osrm``. Hasta 200 puntos distintos. 1 unidad por elemento.
        """
        locs = [
            {"lat": p["lat"], "lon": p["lon"]} if isinstance(p, Mapping) else {"lat": p[0], "lon": p[1]}
            for p in locations
        ]
        body = _drop_none(
            {
                "locations": locs,
                "departure_time": departure_time,
                "sources": sources,
                "destinations": destinations,
                "model": model,
            }
        )
        return self.request("POST", "/v1/matrix", json_body=body)

    @staticmethod
    def _routes(routes: Union[Sequence[Route], Sequence[Stop]]) -> List[Dict[str, Any]]:
        routes = list(routes)
        if routes and isinstance(routes[0], Mapping) and "lat" in routes[0]:
            return [{"stops": routes}]  # una sola ruta dada como lista de paradas
        return [dict(r) for r in routes]  # type: ignore[arg-type]

    def route_traffic(
        self,
        routes: Union[Sequence[Route], Sequence[Stop]],
        *,
        date: Optional[str] = None,
        radius_m: Optional[int] = None,
        max_incidents: Optional[int] = None,
    ) -> JSON:
        """Incidencias DGT cerca de las paradas de una o varias rutas (``POST /v1/traffic/route-incidents``).

        ``routes``: lista de rutas ``{"id"?, "date"?, "stops": [{"lat", "lon", "id"?, "time"?}]}`` o directamente
        una lista de paradas (una sola ruta). 1 unidad por ruta.
        """
        body = _drop_none(
            {"routes": self._routes(routes), "date": date, "radius_m": radius_m, "max_incidents": max_incidents}
        )
        return self.request("POST", "/v1/traffic/route-incidents", json_body=body)

    def route_weather(
        self,
        routes: Union[Sequence[Route], Sequence[Stop]],
        *,
        date: Optional[str] = None,
        min_warning_level: Optional[str] = None,
    ) -> JSON:
        """Tiempo AEMET en cada parada a su hora y avisos que la afectan (``POST /v1/weather/route-conditions``).

        ``min_warning_level``: ``yellow`` (por defecto), ``orange`` o ``red``. 1 unidad por ruta.
        """
        body = _drop_none(
            {"routes": self._routes(routes), "date": date, "min_warning_level": min_warning_level}
        )
        return self.request("POST", "/v1/weather/route-conditions", json_body=body)

    def weather_forecast(self, lat: float, lon: float) -> JSON:
        """Previsión AEMET para un punto (``GET /v1/weather/forecast``). 1 unidad."""
        return self.request("GET", "/v1/weather/forecast", params={"lat": lat, "lon": lon})

    def weather_warnings(
        self, lat: float, lon: float, *, date: Optional[str] = None, min_level: Optional[str] = None
    ) -> JSON:
        """Avisos AEMET para un punto (``GET /v1/weather/warnings``). 1 unidad."""
        return self.request(
            "GET", "/v1/weather/warnings", params={"lat": lat, "lon": lon, "date": date, "min_level": min_level}
        )

    def weather_history(self, lat: float, lon: float, date_from: str, date_to: str) -> JSON:
        """Tiempo observado entre dos fechas (``GET /v1/weather/history``; ``date_to`` como mucho ayer). 1 unidad."""
        return self.request(
            "GET", "/v1/weather/history", params={"lat": lat, "lon": lon, "from": date_from, "to": date_to}
        )

    def me(self) -> Account:
        """Plan, saldo, franquicias y límites de tu cuenta (``GET /v1/me``). Gratis."""
        return self.request("GET", "/v1/me")

    def uso(self, mes: Optional[str] = None) -> Usage:
        """Consumo del mes por día, producto y canal (``GET /v1/uso``; ``mes`` = ``AAAA-MM``). Gratis."""
        return self.request("GET", "/v1/uso", params={"mes": mes})

    usage = uso
