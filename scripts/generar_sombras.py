"""Genera, para cada minuto de interes del eclipse del 12/08/2026 en la zona
Cehegin+Bullas+Mula+Pliego, un raster de visibilidad del sol (visible /
oculto por el relieve), usando el MDT05 del IGN y la posicion solar real
(skyfield, DE421).
"""
from osgeo import gdal

import json
import os
from datetime import datetime, timedelta, timezone

import numpy as np
from skyfield.api import load, wgs84

from shadow_utils import compute_shadow_mask

gdal.UseExceptions()

BASE = r"C:\Users\INGEMISUR\Downloads\Eclipse_Murcia_Bullas"
DEM_PATH = os.path.join(BASE, "MDT05_extendido.tif")
OUT_DIR = os.path.join(BASE, "frames")

# punto de referencia para calcular la posicion solar (az/alt); a la
# distancia del sol la diferencia de paralaje entre puntos separados por
# 40 km es despreciable, asi que un unico punto (Bullas, centrico en la
# zona) sirve para toda la extension del modelo.
BULLAS_LAT = 38.0468805639948700
BULLAS_LON = -1.6677949475113110
BULLAS_ELEV_M = 600

START_LOCAL = datetime(2026, 8, 12, 19, 45, tzinfo=timezone(timedelta(hours=2)))
END_LOCAL = datetime(2026, 8, 12, 21, 5, tzinfo=timezone(timedelta(hours=2)))
STEP_MIN = 5


def cargar_dem():
    ds = gdal.Open(DEM_PATH)
    band = ds.GetRasterBand(1)
    elev = band.ReadAsArray().astype(np.float32)
    gt = ds.GetGeoTransform()
    proj = ds.GetProjection()
    pixel_size = gt[1]
    return elev, gt, proj, pixel_size, ds.RasterXSize, ds.RasterYSize


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    elev, gt, proj, pixel_size, w, h = cargar_dem()
    print(f"DEM: {w}x{h} px, pixel={pixel_size}m")

    eph = load('de421.bsp')
    ts = load.timescale()
    sun = eph['sun']
    earth = eph['earth']
    observer = earth + wgs84.latlon(BULLAS_LAT, BULLAS_LON, elevation_m=BULLAS_ELEV_M)

    driver = gdal.GetDriverByName("GTiff")

    t = START_LOCAL
    resumen = []
    while t <= END_LOCAL:
        ts_t = ts.from_datetime(t)
        alt_sun, az_sun, _ = observer.at(ts_t).observe(sun).apparent().altaz()
        alt = alt_sun.degrees
        az = az_sun.degrees

        if alt <= 0:
            print(f"{t.strftime('%H:%M')}  sol bajo el horizonte (alt={alt:.2f}), se omite")
            t += timedelta(minutes=STEP_MIN)
            continue

        shadow = compute_shadow_mask(elev, pixel_size, az, alt)
        pct_oculto = 100.0 * shadow.sum() / shadow.size

        # raster de salida: 0 = oculto por relieve, 1 = sol visible
        visible = (~shadow).astype(np.uint8)

        out_path = os.path.join(OUT_DIR, f"vis_{t.strftime('%H%M')}.tif")
        out_ds = driver.Create(out_path, w, h, 1, gdal.GDT_Byte,
                                options=["COMPRESS=DEFLATE"])
        out_ds.SetGeoTransform(gt)
        out_ds.SetProjection(proj)
        out_ds.GetRasterBand(1).WriteArray(visible)
        out_ds.GetRasterBand(1).SetNoDataValue(255)
        out_ds = None

        print(f"{t.strftime('%H:%M')}  az={az:7.2f} alt={alt:5.2f}  oculto={pct_oculto:5.1f}%  -> {out_path}")
        resumen.append((t.strftime('%H:%M'), az, alt, pct_oculto))
        t += timedelta(minutes=STEP_MIN)

    print("\nResumen:")
    for hhmm, az, alt, pct in resumen:
        print(f"  {hhmm}  az={az:.1f} alt={alt:.2f}  %oculto_relieve={pct:.1f}")

    resumen_path = os.path.join(BASE, "_trabajo", "_resumen_sombras.json")
    with open(resumen_path, "w", encoding="utf-8") as f:
        json.dump(
            [{"hora": h, "az": az, "alt": alt, "pct_oculto": pct} for h, az, alt, pct in resumen],
            f, ensure_ascii=False, indent=2,
        )
    print("\nResumen guardado en", resumen_path)


if __name__ == "__main__":
    main()
