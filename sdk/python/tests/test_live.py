"""Pruebas contra la API real. Necesitan GEO_GOVOY_API_KEY; consumen unas pocas unidades.

    GEO_GOVOY_API_KEY=... pytest tests/test_live.py
"""
import datetime as dt
import os

import pytest

from geo_govoy import AuthenticationError, GeoGovoy, ValidationError

pytestmark = pytest.mark.skipif(not os.environ.get("GEO_GOVOY_API_KEY"), reason="sin GEO_GOVOY_API_KEY")

MADRID = {"lat": 40.4193, "lon": -3.6916}
BCN = {"lat": 41.3874, "lon": 2.1686}


@pytest.fixture(scope="module")
def geo():
    return GeoGovoy()


def test_me(geo):
    me = geo.me()
    assert me["status"] == "activa"
    assert "limits" in me


def test_uso(geo):
    u = geo.uso()
    assert "totales" in u and "dias" in u
    assert u["mes"] == dt.date.today().strftime("%Y-%m")


def test_geocode(geo):
    r = geo.geocode(["Calle de Alcalá 50, 28014 Madrid", {"external_id": "b", "raw_address": "Avda. Diagonal 640, Barcelona"}])
    assert r["total"] == 2
    c = r["results"][0]["candidates"][0]
    assert abs(c["lat"] - 40.419) < 0.01 and abs(c["lon"] + 3.69) < 0.01
    assert r["results"][1]["external_id"] == "b"
    assert r["results"][0]["next_action"]
    assert geo.last_quota.get("remaining") is not None


def test_reverse(geo):
    r = geo.reverse_geocode([(40.4193, -3.6916)])
    assert r["total"] == 1
    assert r["results"][0]["candidates"]


def test_matrix(geo):
    m = geo.matrix([MADRID, BCN], departure_time="08:30")
    assert len(m["durations"]) == 2
    assert m["durations"][0][1] > 3 * 3600  # Madrid-Barcelona, más de 3 h
    assert m["distances"][0][1] > 500_000


def test_route_traffic(geo):
    r = geo.route_traffic([{"lat": 40.4193, "lon": -3.6916, "time": "09:00"}, {"lat": 40.45, "lon": -3.69, "time": "09:30"}])
    assert isinstance(r, dict) and "routes" in r


def test_route_weather(geo):
    r = geo.route_weather([{"id": "r1", "stops": [{"lat": 40.4193, "lon": -3.6916, "time": "10:00"}]}])
    assert isinstance(r, dict) and "routes" in r


def test_bad_key():
    with pytest.raises(AuthenticationError) as e:
        GeoGovoy("clave-que-no-existe").me()
    assert e.value.status == 401 and e.value.code == "invalid_api_key"


def test_422_too_many(geo):
    with pytest.raises(ValidationError) as e:
        geo.request("POST", "/v2/geocode", json_body={"items": [{"raw_address": "x"}] * 1001})
    assert e.value.status == 422
