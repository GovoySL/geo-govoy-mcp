<p align="center">
  <img src="assets/geo-icon-512.png" alt="Geo Govoy" width="128" height="128">
</p>

<h1 align="center">Geo Govoy MCP</h1>

<p align="center">
  Street and road data for planning delivery routes in Spain, as a remote MCP server and a REST API.<br>
  <a href="https://geo.govoy.es">geo.govoy.es</a> ·
  <a href="https://govoy.es/geo/precios/">Pricing</a> ·
  <a href="https://geo.govoy.es/docs">API reference</a> ·
  <a href="https://geo.govoy.es/fuentes">Sources</a> ·
  <a href="https://stats.uptimerobot.com/DbZWFwwWMj">Status</a> ·
  <a href="#español">Español</a>
</p>

---

## English

**Geo Govoy** gives your AI agent the street and road data it needs to plan delivery routes in **Spain**:
geocoding for Spanish addresses, road travel-time matrices that depend on the departure time, DGT traffic
incidents near each stop and AEMET weather and warnings at each stop at the time you get there.

It is built by [Govoy](https://govoy.es), a Spanish company that builds AI agents for logistics and transport.
Geo opens the same street and road APIs that Govoy's own agents use.

This repository holds **documentation only** (how to connect, tools, configuration). The server is hosted by
Govoy; there is nothing to install or run locally.

| | |
|---|---|
| MCP endpoint | `https://geo.govoy.es/mcp` |
| Transport | Streamable HTTP (remote, stateless) |
| Authentication | OAuth (claude.ai, Claude app, ChatGPT) or `Authorization: Bearer <key>` (also accepts `X-API-Key: <key>`) |
| Coverage | Spain only |
| Customers | Businesses and self-employed with a Spanish tax ID (NIF) |
| REST API | `https://geo.govoy.es` · OpenAPI at [`/openapi.json`](https://geo.govoy.es/openapi.json) · [Swagger](https://geo.govoy.es/docs) |

### Tools

All 9 tools are read-only. The same key, quotas and unit price apply over MCP and over the REST API.

| Tool | What it does | Units |
|---|---|---|
| `geocode_addresses` | Turns Spanish addresses into coordinates (up to 50 per call). Each result comes with a status, a next action (accept, confirm, fix) and the reason | 1 per distinct address |
| `reverse_geocode` | Returns the nearest address for coordinates (up to 50 points) | 1 per point |
| `travel_times` | Road time and distance matrix by departure time (up to 25 places), from Govoy's own driving model | 1 per matrix element |
| `route_traffic` | DGT traffic incidents (roadworks, closures, accidents) near the stops of one or more routes, at the time you pass by | 1 per route |
| `route_weather` | AEMET weather at each stop at its time, and the warnings that affect it | 1 per route |
| `weather_forecast` | AEMET forecast for a place | 1 |
| `weather_warnings` | Active AEMET warnings for a place | 1 |
| `weather_history` | Weather observed on past days at a place | 1 |
| `my_usage` | Plan, limits and usage of your account this month | free |

Places can be given as an address or as `lat`/`lon`; addresses are geocoded first (1 geocoding unit each).
MCP limits are lower than the API's (50 addresses, 25 places in `travel_times`, 20 routes and 500 stops) so that
results fit in the model's context. For large volumes, use the [REST API](https://geo.govoy.es).

### Get a key

Write to **admin@govoy.es** (subject: "Clave de la API de GOVOY") from your company address. Self-service sign-up
at [geo.govoy.es](https://geo.govoy.es) is coming soon. There is a free monthly allowance; paid plans start at
29 €/month. See [pricing](https://govoy.es/geo/precios/).

Treat the key like a password: never put it in a URL, in published code or in a web page that runs in the browser.

### Configuration

#### Claude.ai and the Claude app (OAuth)

1. Settings → Connectors → **Add custom connector**.
2. Server URL: `https://geo.govoy.es/mcp`. Leave client ID and secret empty (dynamic client registration).
3. A Govoy page opens: paste your key and click **Permitir** (Allow). The app gets its own grant, not your key.

#### ChatGPT (OAuth)

1. Settings → Apps & Connectors → Advanced → enable **developer mode**.
2. Create a new connector with URL `https://geo.govoy.es/mcp` and OAuth authentication.
3. On the Govoy page, paste your key and click **Permitir**.

#### Claude Code

```bash
claude mcp add --transport http geo-govoy https://geo.govoy.es/mcp --header "Authorization: Bearer YOUR_KEY"
```

Without the header, Claude Code can also connect with OAuth (`/mcp` → authenticate).

#### Cursor (`.cursor/mcp.json` or `~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "geo-govoy": {
      "url": "https://geo.govoy.es/mcp",
      "headers": { "Authorization": "Bearer YOUR_KEY" }
    }
  }
}
```

#### VS Code (`.vscode/mcp.json`)

```json
{
  "inputs": [
    { "type": "promptString", "id": "geo-govoy-key", "description": "Geo Govoy API key", "password": true }
  ],
  "servers": {
    "geo-govoy": {
      "type": "http",
      "url": "https://geo.govoy.es/mcp",
      "headers": { "Authorization": "Bearer ${input:geo-govoy-key}" }
    }
  }
}
```

#### Your own agent

Any MCP client that speaks streamable HTTP, with the `Authorization: Bearer YOUR_KEY` header.

### Example prompts

1. "Geocode these delivery addresses in Spain and tell me which ones need review and why."
2. "How long between these 10 stops leaving at 7:30 tomorrow from Lorca? And at 10:00?"
3. "Tomorrow's route passes these stops at these times: any DGT incidents or AEMET warnings?"
4. "How much of my monthly allowance is left?"

### Examples, integrations and resources

- [`examples/`](examples/): ready-to-run calls with curl, Python and JavaScript.
- [`integrations/`](integrations/): Postman collection, n8n, Make and Claude Code (`/geo-ruta`).
- [Postman workspace](https://www.postman.com/govoyes/workspace/geo-govoy): public collection and environment, fork and add your key.
- [Status page](https://stats.uptimerobot.com/DbZWFwwWMj): uptime of the REST API and the MCP server.
- [CHANGELOG](CHANGELOG.md): public changes to tools, endpoints and limits.

### Data, attribution and limitations

Geo Govoy combines open data from Spanish public bodies and collaborative projects with Govoy's own models.
If you show results to third parties, include this attribution
([details and full list of sources](https://geo.govoy.es/fuentes)):

> © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright) (ODbL) · Obra derivada de CartoCiudad
> y NGBE CC-BY 4.0 [scne.es](https://www.scne.es) · Dirección General del Catastro · Overture Maps Foundation ·
> Fuentes: geo.govoy.es/fuentes

- Traffic incidents: *Fuente: Dirección General de Tráfico (DGT), Punto de Acceso Nacional · actualizado a
  &lt;fecha&gt;* (date from `updated_at`).
- Weather and warnings: *Fuente: AEMET · elaborado el &lt;fecha&gt;* (date from `issued`).

Traffic and weather information is indicative and does not replace official channels. Traffic incidents do not
cover the Basque Country, Catalonia or urban streets. **Neither DGT nor AEMET endorse this service.** Results are
not official cadastral information.

Govoy does not store the content of requests, over MCP or API. What a tool returns reaches the model provider
your agent uses. [Terms](https://geo.govoy.es/terminos) · [Privacy](https://geo.govoy.es/privacidad) ·
[Data processing agreement](https://geo.govoy.es/encargo).

### Support

admin@govoy.es · GOVOY SOLUTIONS SL, Spain.

---

## Español

**Geo Govoy** da a tu agente de IA los datos de calle y carretera que necesita para planificar rutas de reparto
en **España**: geocodificación de direcciones españolas, matrices de tiempos por carretera según la hora de
salida, incidencias de la DGT cerca de cada parada y el tiempo y los avisos de AEMET en cada parada a su hora.

Lo hace [Govoy](https://govoy.es), empresa española que desarrolla agentes de IA para logística y transporte.
Geo abre las mismas APIs de calle y carretera que usan los agentes de Govoy.

Este repositorio contiene **solo documentación** (cómo conectarse, herramientas, configuración). El servidor lo
aloja Govoy: no hay nada que instalar ni ejecutar en local.

| | |
|---|---|
| URL MCP | `https://geo.govoy.es/mcp` |
| Transporte | HTTP streamable (remoto, sin sesión) |
| Autenticación | OAuth (claude.ai, app de Claude, ChatGPT) o `Authorization: Bearer <clave>` (también `X-API-Key: <clave>`) |
| Cobertura | Solo España |
| Clientes | Empresas y autónomos con NIF español |
| API REST | `https://geo.govoy.es` · OpenAPI en [`/openapi.json`](https://geo.govoy.es/openapi.json) · [Swagger](https://geo.govoy.es/docs) |

### Herramientas

Las 9 son de solo lectura. Misma clave, mismas cuotas y mismo precio por unidad por MCP que por la API REST.

| Herramienta | Qué hace | Unidades |
|---|---|---|
| `geocode_addresses` | Convierte direcciones españolas en coordenadas (hasta 50 por llamada), con estado, siguiente acción (aceptar, confirmar, corregir) y motivo | 1 por dirección distinta |
| `reverse_geocode` | Devuelve la dirección más cercana a unas coordenadas (hasta 50 puntos) | 1 por punto |
| `travel_times` | Matriz de tiempos y distancias por carretera según la hora de salida (hasta 25 lugares), con el modelo de conducción propio de Govoy | 1 por elemento |
| `route_traffic` | Incidencias de la DGT (obras, cortes, accidentes) cerca de las paradas de una o varias rutas, a la hora de paso | 1 por ruta |
| `route_weather` | Tiempo de AEMET en cada parada a su hora y los avisos que le afectan | 1 por ruta |
| `weather_forecast` | Previsión de AEMET para un lugar | 1 |
| `weather_warnings` | Avisos de AEMET vigentes en un lugar | 1 |
| `weather_history` | Tiempo observado en días pasados en un lugar | 1 |
| `my_usage` | Plan, límites y consumo del mes | gratis |

Los lugares se indican por dirección o por `lat`/`lon`; las direcciones se geocodifican antes (1 unidad de
geocodificación cada una). Los topes por MCP son más bajos que los de la API (50 direcciones, 25 lugares en
`travel_times`, 20 rutas y 500 paradas) para que la respuesta quepa en el contexto del modelo. Para volúmenes
grandes, la [API REST](https://geo.govoy.es).

### Pedir una clave

Escribe a **admin@govoy.es** (asunto: «Clave de la API de GOVOY») desde el correo de tu empresa. El alta en
autoservicio en [geo.govoy.es](https://geo.govoy.es) llega en breve. Hay un plan gratis cada mes; los planes de
pago empiezan en 29 €/mes. Consulta los [precios](https://govoy.es/geo/precios/).

Guarda la clave como una contraseña: nunca en una URL, en código publicado ni en una web que se ejecute en el
navegador.

### Configuración

**Claude.ai y app de Claude**: Ajustes → Conectores → **Añadir conector personalizado** → URL
`https://geo.govoy.es/mcp` (deja vacíos el ID y el secreto de cliente) → en la página de Govoy, pega tu clave y
pulsa **Permitir**.

**ChatGPT**: Ajustes → Aplicaciones y conectores → Avanzado → activa el **modo desarrollador** → crea un conector
con la URL `https://geo.govoy.es/mcp` y OAuth → pega tu clave y pulsa **Permitir**.

**Claude Code**:

```bash
claude mcp add --transport http geo-govoy https://geo.govoy.es/mcp --header "Authorization: Bearer TU_CLAVE"
```

**Cursor** (`.cursor/mcp.json`) y **VS Code** (`.vscode/mcp.json`): los mismos ficheros de la sección en inglés,
cambiando `YOUR_KEY` por tu clave (en VS Code, `servers` y `"type": "http"`).

**Agente propio**: cualquier cliente MCP por HTTP streamable con la cabecera `Authorization: Bearer TU_CLAVE`.

### Ejemplos de uso

1. «Geocodifica estas direcciones de entrega y dime cuáles tengo que revisar y por qué.»
2. «¿Cuánto se tarda entre estas 10 paradas saliendo mañana a las 7:30 desde Lorca? ¿Y a las 10:00?»
3. «Mi ruta de mañana pasa por estas paradas a estas horas: ¿hay obras, cortes o avisos de lluvia o viento?»
4. «¿Cuánto me queda de saldo este mes?»

### Ejemplos, integraciones y recursos

- [`examples/`](examples/): llamadas listas para usar con curl, Python y JavaScript.
- [`integrations/`](integrations/): colección de Postman, n8n, Make y Claude Code (`/geo-ruta`).
- [Workspace de Postman](https://www.postman.com/govoyes/workspace/geo-govoy): colección y entorno públicos; haz un fork y añade tu clave.
- [Página de estado](https://stats.uptimerobot.com/DbZWFwwWMj): disponibilidad de la API REST y del servidor MCP.
- [CHANGELOG](CHANGELOG.md): cambios públicos en herramientas, endpoints y límites.

### Datos, atribución y limitaciones

Si enseñas resultados a terceros, incluye esta atribución ([detalle y lista completa de fuentes](https://geo.govoy.es/fuentes)):

> © [colaboradores de OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL) · Obra derivada de
> CartoCiudad y NGBE CC-BY 4.0 [scne.es](https://www.scne.es) · Dirección General del Catastro · Overture Maps
> Foundation · Fuentes: geo.govoy.es/fuentes

- Incidencias de tráfico: *Fuente: Dirección General de Tráfico (DGT), Punto de Acceso Nacional · actualizado a
  &lt;fecha&gt;* (fecha de `updated_at`).
- Tiempo y avisos: *Fuente: AEMET · elaborado el &lt;fecha&gt;* (fecha de `issued`).

La información de tráfico y tiempo es orientativa y no sustituye a los canales oficiales. Las incidencias de
tráfico no cubren País Vasco, Cataluña ni vías urbanas. **Ni la DGT ni AEMET respaldan este servicio.** Los
resultados no son información catastral.

Govoy no guarda el contenido de las peticiones, tampoco por el MCP. Lo que devuelve una herramienta llega al
proveedor del modelo que use tu agente. [Términos](https://geo.govoy.es/terminos) ·
[Privacidad](https://geo.govoy.es/privacidad) · [Encargo de tratamiento](https://geo.govoy.es/encargo).

### Soporte

admin@govoy.es · GOVOY SOLUTIONS SL, España.

---

Documentation licensed under [CC BY 4.0](LICENSE) · Documentación bajo licencia [CC BY 4.0](LICENSE).
