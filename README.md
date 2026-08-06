# Eclipse solar del 12 de agosto de 2026 — Cehegín, Bullas, Mula y Pliego

Visor interactivo que muestra, minuto a minuto entre las 19:45 y las 20:55
(hora local), desde qué zonas del término municipal se verá el Sol y desde
cuáles quedará oculto por el relieve durante el eclipse solar parcial del
12/08/2026, para el área de Cehegín, Bullas, Mula y Pliego (Región de
Murcia).

**Ver el visor:** abre `index.html` (o la URL de GitHub Pages una vez
publicado).

## Cómo se calculó

- **Terreno**: MDT05 (paso de malla 5 m) del IGN, descargado vía su
  servicio WCS (`servicios.idee.es/wcs-inspire/mdt`, cobertura
  `Elevacion25830_5`) — ver [`scripts/descargar_mdt_extendido.py`](scripts/descargar_mdt_extendido.py).
- **Posición solar**: efemérides JPL DE421 vía [Skyfield](https://rhodesmill.org/skyfield/),
  calculada para el punto de referencia de Bullas (a la distancia del Sol,
  la diferencia de paralaje entre puntos separados 40 km es despreciable)
  — ver [`scripts/generar_sombras.py`](scripts/generar_sombras.py).
- **Sombra de relieve**: algoritmo de oclusión de horizonte por rotación y
  barrido acumulado sobre la malla de elevaciones — ver
  [`scripts/shadow_utils.py`](scripts/shadow_utils.py).
- **Visualización**: Leaflet + capas de imagen georreferenciadas (una por
  minuto), coloreadas en amarillo (Sol visible) / azul (oculto por
  relieve) — ver [`scripts/generar_visualizacion.py`](scripts/generar_visualizacion.py)
  y [`scripts/construir_html.py`](scripts/construir_html.py).

**Eclipse parcial, no total** — en esta zona el Sol alcanza como mucho una
obscuración de ~98% hacia las 20:35, con una altura solar de solo ~4-5°
sobre el horizonte.
