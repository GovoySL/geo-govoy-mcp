"""Manejo de errores y reintentos contra un servidor local simulado (sin red ni clave)."""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from geo_govoy import (
    AuthenticationError,
    GeoGovoy,
    GeoGovoyError,
    PayloadTooLargeError,
    QuotaExceededError,
    RateLimitError,
)

STATE = {"calls": 0}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencio
        pass

    def _send(self, status, body, headers=None):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        self._route()

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self.body = json.loads(self.rfile.read(n) or b"{}")
        self._route()

    def _route(self):
        STATE["calls"] += 1
        p = self.path
        if p == "/401":
            self._send(401, {"detail": {"error": "invalid_api_key", "message": "API key invalida o ausente."}})
        elif p == "/402":
            self._send(402, {"detail": {"error": "quota_exceeded", "message": "Cuota agotada"}})
        elif p == "/413":
            self._send(413, {"detail": {"error": "payload_too_large", "message": "Demasiado grande"}})
        elif p == "/429-always":
            self._send(429, {"detail": {"error": "rate_limit", "message": "Espera"}}, {"Retry-After": "0"})
        elif p == "/429-once":
            if STATE["calls"] == 1:
                self._send(429, {"detail": {"error": "rate_limit", "message": "Espera"}}, {"Retry-After": "1"})
            else:
                self._send(200, {"ok": True}, {"X-Govoy-Quota-Remaining": "41", "X-Govoy-Quota-Limit": "100",
                                               "X-Govoy-Quota-Unit": "units"})
        elif p == "/v2/geocode":
            items = self.body["items"]
            self._send(200, {"request_id": f"r{STATE['calls']}", "results": [
                {"external_id": it.get("external_id"), "input": it, "status": "matched"} for it in items]})
        else:
            self._send(404, {"detail": "Not Found"})


@pytest.fixture()
def geo():
    STATE["calls"] = 0
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield GeoGovoy("test", base_url=f"http://127.0.0.1:{srv.server_port}", max_retries=2)
    srv.shutdown()


def test_missing_key(monkeypatch):
    monkeypatch.delenv("GEO_GOVOY_API_KEY", raising=False)
    with pytest.raises(GeoGovoyError):
        GeoGovoy()


def test_key_from_env(monkeypatch):
    monkeypatch.setenv("GEO_GOVOY_API_KEY", "x")
    assert GeoGovoy().base_url == "https://geo.govoy.es"


def test_401(geo):
    with pytest.raises(AuthenticationError) as e:
        geo.request("GET", "/401")
    assert e.value.status == 401 and e.value.code == "invalid_api_key"


def test_402_not_retried(geo):
    with pytest.raises(QuotaExceededError) as e:
        geo.request("GET", "/402")
    assert e.value.code == "quota_exceeded"
    assert STATE["calls"] == 1


def test_413(geo):
    with pytest.raises(PayloadTooLargeError):
        geo.request("POST", "/413", json_body={"items": []})


def test_429_retry_after_then_ok(geo):
    t0 = time.monotonic()
    assert geo.request("GET", "/429-once") == {"ok": True}
    assert time.monotonic() - t0 >= 0.9  # respetó Retry-After: 1
    assert STATE["calls"] == 2
    assert geo.last_quota == {"limit": 100, "remaining": 41, "unit": "units"}


def test_429_gives_up(geo):
    with pytest.raises(RateLimitError) as e:
        geo.request("GET", "/429-always")
    assert e.value.retry_after == 0
    assert STATE["calls"] == 3  # 1 + 2 reintentos


def test_geocode_batches_keep_order(geo):
    addrs = [f"Calle {i}, Madrid" for i in range(25)]
    r = geo.geocode([{"external_id": str(i), "raw_address": a} for i, a in enumerate(addrs)], batch_size=10)
    assert STATE["calls"] == 3
    assert r["total"] == 25 and len(r["request_ids"]) == 3
    assert [x["external_id"] for x in r["results"]] == [str(i) for i in range(25)]
