"""Monta el index.html final del visor reutilizando la libreria Leaflet
(CSS+JS) embebida, y generando panel/leyenda/datos propios para la zona
de Cehegin, Bullas, Mula y Pliego (Region de Murcia)."""
import json
import os

TRABAJO = r"C:\Users\INGEMISUR\Downloads\Eclipse_Murcia_Bullas\_trabajo"
SITE_DIR = os.path.join(TRABAJO, "site")

with open(os.path.join(TRABAJO, "_leaflet_head.html"), encoding="utf-8") as f:
    head = f.read()

with open(os.path.join(TRABAJO, "_data.json"), encoding="utf-8") as f:
    payload = json.load(f)

with open(os.path.join(TRABAJO, "_municipios.geojson"), encoding="utf-8") as f:
    municipios_geojson = json.load(f)

data = payload["data"]
bounds = payload["bounds"]

# ---- cabecera: titulo propio, misma libreria Leaflet embebida ----
head = head.replace(
    "<title></title>",
    "<title>Eclipse solar · 12 agosto 2026 · Cehegín, Bullas, Mula y Pliego (Región de Murcia)</title>",
)

marks_horas = ["19:45", "20:05", "20:25", "20:45", "20:55"]
marks_html = "".join(f"<span>{h}</span>" for h in marks_horas)

default_index = next(i for i, d in enumerate(data) if d["hora"] == "20:30")

body = f"""<style>
  html, body {{ margin:0; padding:0; height:100%; font-family:'Segoe UI', system-ui, sans-serif; }}
  #map {{ position:absolute; inset:0; }}
  .panel {{
    position:absolute; left:50%; transform:translateX(-50%); bottom:18px; z-index:1000;
    background:rgba(15,17,26,.88); color:#fff; border-radius:14px; padding:14px 22px 12px;
    width:min(560px, calc(100vw - 40px)); box-shadow:0 6px 24px rgba(0,0,0,.45);
    backdrop-filter: blur(6px);
  }}
  .panel h1 {{ font-size:15px; margin:0 0 2px; font-weight:600; letter-spacing:.2px; }}
  .panel .sub {{ font-size:11.5px; color:#9aa3b5; margin-bottom:8px; }}
  .rowtime {{ display:flex; align-items:baseline; gap:12px; margin-bottom:4px; }}
  #hora {{ font-size:30px; font-weight:700; font-variant-numeric:tabular-nums; }}
  #fase {{ font-size:12.5px; font-weight:600; padding:3px 10px; border-radius:20px; background:#2b3350; }}
  #fase.maximo {{ background:#b8492f; }}
  #datos {{ font-size:12px; color:#c6cddd; margin-bottom:6px; }}
  input[type=range] {{ width:100%; accent-color:#ffd700; cursor:pointer; }}
  .marks {{ display:flex; justify-content:space-between; font-size:10px; color:#8790a5; margin-top:2px; }}
  .controls {{ display:flex; align-items:center; gap:10px; margin-top:6px; }}
  .controls button {{
    background:#ffd700; color:#1a1a1a; border:none; border-radius:8px; font-weight:700;
    padding:5px 14px; cursor:pointer; font-size:12.5px;
  }}
  .controls label {{ font-size:11.5px; color:#c6cddd; display:flex; align-items:center; gap:6px; }}
  .legend {{ position:absolute; top:14px; right:14px; z-index:1000; background:rgba(15,17,26,.85);
    color:#fff; border-radius:10px; padding:10px 14px; font-size:12px; line-height:1.9; }}
  .sw {{ display:inline-block; width:14px; height:14px; border-radius:3px; vertical-align:-2px; margin-right:7px; }}
  .credit {{ position:absolute; top:14px; left:14px; z-index:1000; background:rgba(15,17,26,.85);
    color:#c6cddd; border-radius:10px; padding:8px 12px; font-size:11px; max-width:290px; }}
  .muni-label {{ background:none; border:none; box-shadow:none; color:#fff; font-size:11.5px;
    font-weight:600; text-shadow:0 0 4px #000, 0 0 4px #000, 0 1px 2px #000; white-space:nowrap; }}
</style>
</head>
<body>
<div id="map"></div>

<div class="credit"><b style="color:#fff">Eclipse parcial · Cehegín, Bullas, Mula y Pliego (Murcia)</b><br>
¿Desde donde se vera el sol en cada minuto? Con el sol a solo 1-14° de altura, el relieve de la Sierra decide.
Sombras calculadas sobre el MDT05 (5 m) del IGN.</div>

<div class="legend">
  <span class="sw" style="background:rgba(255,215,0,.75)"></span>Sol visible<br>
  <span class="sw" style="background:rgba(45,45,110,.8)"></span>Oculto por el relieve
</div>

<div class="panel">
  <h1>Eclipse solar — 12 de agosto de 2026</h1>
  <div class="sub">Cehegín, Bullas, Mula y Pliego, Región de Murcia · máximo ≈20:35-20:36 (alt. ~4.5°) · puesta de sol ≈21:00 · eclipse parcial (sin totalidad)</div>
  <div class="rowtime"><span id="hora">20:30</span><span id="fase">Parcial</span></div>
  <div id="datos"></div>
  <input id="slider" type="range" min="0" max="{len(data) - 1}" step="1" value="{default_index}">
  <div class="marks">{marks_html}</div>
  <div class="controls">
    <button id="play">▶ Reproducir</button>
    <label>opacidad <input id="opac" type="range" min="20" max="100" value="100" style="width:90px;accent-color:#ffd700"></label>
  </div>
</div>

<script>
const DATA = {json.dumps(data, ensure_ascii=False)};
const BOUNDS = {json.dumps(bounds)};
const MUNICIPIOS = {json.dumps(municipios_geojson, ensure_ascii=False)};

const map = L.map('map', {{ zoomSnap: 0.25 }});
map.fitBounds(BOUNDS);
L.tileLayer('https://mt{{s}}.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
  subdomains:['0','1','2','3'], maxZoom:20, attribution:'Imágenes © Google'
}}).addTo(map);

const overlays = DATA.map(d => L.imageOverlay(d.img, BOUNDS, {{ opacity: 0 }}).addTo(map));

const municipiosLayer = L.geoJSON(MUNICIPIOS, {{
  style: {{ color: '#f2f2f2', weight: 1.6, opacity: .65, fillOpacity: 0 }},
}}).addTo(map);
municipiosLayer.eachLayer(function (l) {{
  const nombre = l.feature.properties.nombre;
  const c = l.getBounds().getCenter();
  L.marker(c, {{
    icon: L.divIcon({{ className: 'muni-label', html: nombre, iconSize: [120, 16], iconAnchor: [60, 8] }}),
    interactive: false,
  }}).addTo(map);
}});
let cur = -1;
const elH = document.getElementById('hora'), elF = document.getElementById('fase'),
      elD = document.getElementById('datos'), sl = document.getElementById('slider');

function fase(hora) {{
  if (hora === '20:35') return ['Fase máxima', true];
  return ['Eclipse parcial', false];
}}
function show(i) {{
  i = +i;
  const op = document.getElementById('opac').value / 100;
  overlays.forEach((o, k) => o.setOpacity(k === i ? op : 0));
  const d = DATA[i];
  elH.textContent = d.hora;
  const [txt, max] = fase(d.hora);
  elF.textContent = txt; elF.className = max ? 'maximo' : '';
  elD.innerHTML = 'Sol: altura <b>' + d.alt.toFixed(1) + '°</b> · azimut <b>' + d.az.toFixed(0) + '°</b> (ONO) &nbsp;·&nbsp; <b>' +
                  d.pct.toFixed(0) + '%</b> de la zona con visión directa del sol';
  cur = i;
}}
sl.addEventListener('input', e => show(e.target.value));
document.getElementById('opac').addEventListener('input', () => show(cur));

let timer = null;
document.getElementById('play').addEventListener('click', function () {{
  if (timer) {{ clearInterval(timer); timer = null; this.textContent = '▶ Reproducir'; return; }}
  this.textContent = '⏸ Pausa';
  timer = setInterval(() => {{
    let n = (+sl.value + 1) % {len(data)};
    sl.value = n; show(n);
  }}, 900);
}});
show({default_index});
</script>
</body>
</html>
"""

final_html = head + body
with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(final_html)

print("index.html generado:", os.path.join(SITE_DIR, "index.html"))
print("bytes:", len(final_html))
