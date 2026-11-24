# Claude Code · Geo Govoy como servidor MCP + comando `/geo-ruta`

## 1. Añadir el MCP

Con clave (recomendado para uso en terminal):

```bash
claude mcp add --transport http geo-govoy https://geo.govoy.es/mcp \
  --header "Authorization: Bearer $GEO_API_KEY"
```

Sin clave en la configuración (OAuth): añade el servidor sin `--header`, abre Claude Code, escribe `/mcp`,
elige `geo-govoy` → **Authenticate**, pega tu clave en la página de Govoy y pulsa **Permitir**.

Para compartirlo con tu equipo dentro de un repo, usa `--scope project` (crea `.mcp.json`) y deja que cada
persona ponga su clave en su entorno:

```json
{
  "mcpServers": {
    "geo-govoy": {
      "type": "http",
      "url": "https://geo.govoy.es/mcp",
      "headers": { "Authorization": "Bearer ${GEO_API_KEY}" }
    }
  }
}
```

Comprueba con `claude mcp list` o `/mcp`: deben aparecer 9 herramientas (`geocode_addresses`,
`reverse_geocode`, `travel_times`, `route_traffic`, `route_weather`, `weather_forecast`, `weather_warnings`,
`weather_history`, `my_usage`).

## 2. Comando `/geo-ruta`

[`.claude/commands/geo-ruta.md`](.claude/commands/geo-ruta.md) es un slash command que, a partir de una lista de
direcciones y una hora de salida, geocodifica, calcula tiempos, mira DGT y AEMET y propone el orden de visita.

Instalación: copia el archivo a `.claude/commands/` de tu proyecto (o a `~/.claude/commands/` para todos).

```bash
mkdir -p .claude/commands
curl -sL https://raw.githubusercontent.com/GovoySL/geo-govoy-mcp/main/integrations/claude-code/.claude/commands/geo-ruta.md \
  -o .claude/commands/geo-ruta.md
```

Uso:

```
/geo-ruta 08:30 Calle de Alcalá 50 Madrid; Paseo de la Castellana 200 Madrid; Calle Mayor 1 Getafe; Avenida de Europa 10 Pozuelo
```

También puedes convertirlo en skill (`.claude/skills/geo-ruta/SKILL.md` con el mismo cuerpo y un `description`
en el frontmatter) para que Claude lo use solo cuando hables de rutas de reparto.

## Unidades
Cada llamada consume las mismas unidades que la API REST: 1 por dirección, 1 por elemento de matriz, 1 por ruta
en DGT y AEMET. `my_usage` es gratis. Detalle en [govoy.es/geo/precios](https://govoy.es/geo/precios/).
