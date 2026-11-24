# Postman · Geo Govoy API

**Workspace público:** https://www.postman.com/govoyes/geo-govoy (haz *Fork* de la colección «Geo Govoy API»
y del entorno «Geo Govoy» a tu espacio).

- [`geo-govoy.postman_collection.json`](geo-govoy.postman_collection.json): colección con un ejemplo por endpoint
  (geocodificación con `raw_address`, inversa, matriz por hora, DGT, AEMET, `/v1/me`, `/v1/uso`).
- [`geo-govoy.postman_environment.json`](geo-govoy.postman_environment.json): entorno con `baseUrl` y
  `GEO_API_KEY` vacía.

Importa los dos archivos (**Import** en Postman), elige el entorno «Geo Govoy», pon tu clave en `GEO_API_KEY`
(pídela en admin@govoy.es) y lanza cualquier petición. La clave va en la cabecera `X-API-Key`, configurada en la
autorización de la colección.

También puedes generar la colección desde el OpenAPI: **Import → `https://geo.govoy.es/openapi.json`**.
