"""Geo Govoy · ejemplo mínimo en Python (API REST, solo España).

    pip install requests
    export GEO_API_KEY="tu_clave"      # pídela en admin@govoy.es
    python geo_govoy.py

Docs: https://geo.govoy.es/docs · OpenAPI: https://geo.govoy.es/openapi.json
"""
import os

import requests

BASE = "https://geo.govoy.es"
session = requests.Session()
session.headers.update({"X-API-Key": os.environ["GEO_API_KEY"]})


def post(path: str, body: dict) -> dict:
    r = session.post(f"{BASE}{path}", json=body, timeout=60)
    if r.status_code == 402:
        raise SystemExit("Cuota agotada (402 quota_exceeded)")
    if r.status_code == 429:
        raise SystemExit(f"Demasiadas peticiones (429). Reintenta en {r.headers.get('Retry-After', '?')} s")
    r.raise_for_status()
    return r.json()


# 1. Geocodificar direcciones en texto libre (raw_address)
direcciones = [
    "Calle de Alcalá 50, 28014 Madrid",
    "Avda. Diagonal 640, Barcelona",
    "Plaza del Ayuntamiento 1, Valencia",
]
geo = post("/v2/geocode", {"items": [{"external_id": str(i), "raw_address": d} for i, d in enumerate(direcciones)]})
puntos = []
for res in geo["results"]:
    cand = (res.get("candidates") or [None])[0]
    if cand:
        print(f"{res['external_id']}: {cand['formatted_address']} -> {cand['lat']}, {cand['lon']} "
              f"(confianza {cand['confidence_score']:.2f})")
        puntos.append({"lat": cand["lat"], "lon": cand["lon"]})
    else:
        print(f"{res['external_id']}: sin resultado")

# 2. Matriz de tiempos a las 08:30 con el modelo de conducción de Govoy
if len(puntos) >= 2:
    m = post("/v1/matrix", {"locations": puntos, "departure_time": "08:30", "model": "govoy"})
    for i, fila in enumerate(m["durations"]):
        print(f"desde {i}:", [None if s is None else round(s / 60) for s in fila], "min")

# 3. Incidencias DGT cerca de las paradas de la ruta
inc = post("/v1/traffic/route-incidents", {"routes": [{"id": "ruta-1", "stops": puntos}]})
print("Incidencias DGT:", inc)

# 4. Consumo del mes (gratis)
print(session.get(f"{BASE}/v1/me", timeout=30).json())
