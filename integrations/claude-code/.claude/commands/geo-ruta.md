---
description: Planifica una ruta de reparto en España con Geo Govoy (direcciones, tiempos por hora, DGT y AEMET)
argument-hint: <HH:MM> <dirección 1>; <dirección 2>; ...
allowed-tools: mcp__geo-govoy__geocode_addresses, mcp__geo-govoy__travel_times, mcp__geo-govoy__route_traffic, mcp__geo-govoy__route_weather, mcp__geo-govoy__my_usage
---

Planifica una ruta de reparto con el servidor MCP `geo-govoy`.

Entrada: $ARGUMENTS
- El primer valor es la hora de salida (`HH:MM`). Si no hay hora, usa 08:00.
- El resto son direcciones separadas por `;`. La primera es el almacén (origen y vuelta).

Pasos:
1. `geocode_addresses` con todas las direcciones. Si alguna vuelve con `next_action` distinto de aceptar, enséñala
   con su motivo y pregunta antes de seguir (no inventes coordenadas).
2. `travel_times` con los puntos y `departure_time` = la hora de salida. Con la matriz, ordena las paradas por
   vecino más cercano desde el almacén y mejora el orden con 2-opt. Calcula la hora estimada de llegada a cada
   parada (suma 5 minutos de servicio por parada).
3. `route_traffic` con la ruta ordenada y la hora de paso de cada parada.
4. `route_weather` con la misma ruta y horas.
5. Responde con:
   - Tabla: orden, dirección normalizada, llegada estimada, minutos desde la parada anterior, km.
   - Total de tiempo y km, hora de vuelta al almacén.
   - Incidencias DGT y avisos AEMET que afecten a alguna parada, con la parada afectada.
   - Unidades consumidas (llama a `my_usage` al final).

Sé breve. Solo España.
