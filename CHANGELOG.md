# Changelog

Cambios publicados de Geo Govoy (API REST y servidor MCP). Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Fechas en formato AAAA-MM-DD.

## [2026-11-24] Lanzamiento público

### Añadido
- **API REST pública** en `https://geo.govoy.es` ([Swagger](https://geo.govoy.es/docs) ·
  [OpenAPI](https://geo.govoy.es/openapi.json)), solo España:
  - `POST /v2/geocode`: geocodificación de direcciones españolas (texto libre `raw_address` o por campos), hasta
    1.000 por petición, con `status`, `next_action` y candidatos con confianza.
  - `POST /v1/reverse-geocode`: geocodificación inversa (modos `standard` y `gps`).
  - `POST /v1/matrix`: matriz de tiempos y distancias por carretera según la hora de salida, con el modelo propio
    govoy-conduccion-v1 (o OSRM en bruto).
  - `POST /v1/traffic/route-incidents`: incidencias DGT cerca de las paradas de una o varias rutas.
  - `POST /v1/weather/route-conditions`, `GET /v1/weather/forecast`, `/warnings`, `/history`: tiempo y avisos
    AEMET en ruta, previsión e histórico.
  - `GET /v1/me` y `GET /v1/uso`: plan, límites y consumo (gratis).
  - Cuotas por clave con `402 quota_exceeded`, `429 rate_limit` y cabeceras `X-Govoy-Quota-*`.
- **Servidor MCP remoto** en `https://geo.govoy.es/mcp` (HTTP streamable; Bearer, `X-API-Key` u OAuth para
  claude.ai y ChatGPT) con **9 herramientas** de solo lectura: `geocode_addresses`, `reverse_geocode`,
  `travel_times`, `route_traffic`, `route_weather`, `weather_forecast`, `weather_warnings`, `weather_history`,
  `my_usage`.
- **Tarifa v1.1**: franquicia gratis cada mes por producto (30.000 geocodificaciones, 2.500 elementos de matriz,
  5.000 rutas DGT, 2.500 consultas AEMET), precio por 1.000 con tramos por volumen y planes de prepago en euros
  sin permanencia. Detalle en [govoy.es/geo/precios](https://govoy.es/geo/precios/).
- **Web** [govoy.es/geo](https://govoy.es/geo/) y página de precios.
- Términos, privacidad, encargo de tratamiento y fuentes de datos en [geo.govoy.es](https://geo.govoy.es).
- Este repositorio: README, `server.json`, ejemplos (`examples/`) e integraciones (`integrations/`: Postman, n8n,
  Make, Claude Code).
