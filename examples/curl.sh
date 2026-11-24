#!/usr/bin/env bash
# Geo Govoy · ejemplos mínimos con curl (API REST, solo España)
# Uso:  export GEO_API_KEY="tu_clave"   # pídela en admin@govoy.es
#       bash curl.sh
# Docs: https://geo.govoy.es/docs · OpenAPI: https://geo.govoy.es/openapi.json
set -euo pipefail
: "${GEO_API_KEY:?Define GEO_API_KEY con tu clave}"
BASE="https://geo.govoy.es"

echo "== Cuenta y consumo (/v1/me, gratis)"
curl -s "$BASE/v1/me" -H "X-API-Key: $GEO_API_KEY"; echo

echo "== Geocodificación con raw_address (1 unidad por dirección)"
curl -s -X POST "$BASE/v2/geocode" \
  -H "X-API-Key: $GEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[
        {"external_id":"pedido-1","raw_address":"Calle de Alcalá 50, 28014 Madrid"},
        {"external_id":"pedido-2","raw_address":"Avda. Diagonal 640, Barcelona"}
      ],"top_k":1}'; echo

echo "== Geocodificación inversa (1 unidad por punto)"
curl -s -X POST "$BASE/v1/reverse-geocode" \
  -H "X-API-Key: $GEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"items":[{"lat":40.4189,"lon":-3.6969,"external_id":"gps-1"}],"radius_m":75}'; echo

echo "== Matriz de tiempos según hora de salida (1 unidad por elemento)"
curl -s -X POST "$BASE/v1/matrix" \
  -H "X-API-Key: $GEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"locations":[
        {"lat":40.4168,"lon":-3.7038},
        {"lat":40.4530,"lon":-3.6883},
        {"lat":40.3923,"lon":-3.6995}
      ],"departure_time":"08:30","model":"govoy"}'; echo

echo "== Incidencias DGT cerca de las paradas de una ruta (1 unidad por ruta)"
curl -s -X POST "$BASE/v1/traffic/route-incidents" \
  -H "X-API-Key: $GEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"routes":[{"id":"ruta-1","stops":[
        {"id":"p1","lat":40.4168,"lon":-3.7038,"time":"08:30"},
        {"id":"p2","lat":40.3300,"lon":-3.7700,"time":"09:15"}
      ]}],"radius_m":1000}'; echo

echo "== Tiempo y avisos AEMET en cada parada (1 unidad por ruta)"
curl -s -X POST "$BASE/v1/weather/route-conditions" \
  -H "X-API-Key: $GEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"routes":[{"id":"ruta-1","stops":[
        {"id":"p1","lat":39.4699,"lon":-0.3763,"time":"10:00"},
        {"id":"p2","lat":38.3452,"lon":-0.4810,"time":"12:00"}
      ]}],"min_warning_level":"yellow"}'; echo

echo "== Previsión AEMET en un punto (1 unidad)"
curl -s "$BASE/v1/weather/forecast?lat=37.3891&lon=-5.9845" -H "X-API-Key: $GEO_API_KEY"; echo
