"""Genera las imagenes RGBA para cada frame de visibilidad, reproyectadas
a EPSG:4326 para usarlas como L.imageOverlay en Leaflet."""
from osgeo import gdal

import json
import os

import numpy as np

gdal.UseExceptions()

BASE = r"C:\Users\INGEMISUR\Downloads\Eclipse_Murcia_Bullas"
TRABAJO = os.path.join(BASE, "_trabajo")
FRAMES_DIR = os.path.join(BASE, "frames")
OUT_DIR = os.path.join(TRABAJO, "site", "img")
os.makedirs(OUT_DIR, exist_ok=True)

# Paleta: amarillo para sol visible, azul/indigo para oculto por relieve
COLOR_VISIBLE = (255, 215, 0, 110)   # amarillo dorado pastel translucido
COLOR_SOMBRA = (25, 25, 80, 150)     # azul/indigo pastel translucido
COLOR_NODATA = (0, 0, 0, 0)

with open(os.path.join(TRABAJO, "_resumen_sombras.json"), encoding="utf-8") as f:
    _resumen = json.load(f)
RESUMEN = [(d["hora"], d["az"], d["alt"], d["pct_oculto"]) for d in _resumen]


def warp_a_4326(src_path, dst_path):
    gdal.Warp(dst_path, src_path, dstSRS="EPSG:4326", resampleAlg="near",
              dstNodata=255, format="GTiff")


def colorizar(tif_4326_path, png_path):
    ds = gdal.Open(tif_4326_path)
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray()
    nodata = band.GetNoDataValue()
    gt = ds.GetGeoTransform()
    w, h = ds.RasterXSize, ds.RasterYSize

    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    visible_mask = arr == 1
    sombra_mask = arr == 0
    if nodata is not None:
        valid = arr != nodata
        sombra_mask = sombra_mask & valid

    rgba[visible_mask] = COLOR_VISIBLE
    rgba[sombra_mask] = COLOR_SOMBRA

    driver = gdal.GetDriverByName("MEM")
    mem_ds = driver.Create("", w, h, 4, gdal.GDT_Byte)
    for i in range(4):
        mem_ds.GetRasterBand(i + 1).WriteArray(rgba[:, :, i])
    mem_ds.SetGeoTransform(gt)
    mem_ds.SetProjection(ds.GetProjection())

    png_driver = gdal.GetDriverByName("PNG")
    png_driver.CreateCopy(png_path, mem_ds, strict=0)

    minx = gt[0]
    maxy = gt[3]
    maxx = minx + gt[1] * w
    miny = maxy + gt[5] * h
    return (miny, minx, maxy, maxx)


def main():
    bounds_global = None
    data = []
    for hora, az, alt, pct_oculto in RESUMEN:
        hhmm = hora.replace(":", "")
        src = os.path.join(FRAMES_DIR, f"vis_{hhmm}.tif")
        tmp_4326 = os.path.join(TRABAJO, f"_tmp_{hhmm}_4326.tif")
        warp_a_4326(src, tmp_4326)
        png_name = f"visible_{hhmm}.png"
        png_path = os.path.join(OUT_DIR, png_name)
        bounds = colorizar(tmp_4326, png_path)
        os.remove(tmp_4326)
        if bounds_global is None:
            bounds_global = bounds
        pct_visible = 100.0 - pct_oculto
        data.append({
            "hora": hora, "alt": round(alt, 3), "az": round(az, 3),
            "pct": round(pct_visible, 2), "img": f"img/{png_name}",
        })
        print(f"{hora}  -> {png_name}  (visible {pct_visible:.1f}%)")

    miny, minx, maxy, maxx = bounds_global
    bounds_json = [[miny, minx], [maxy, maxx]]

    with open(os.path.join(TRABAJO, "_data.json"), "w", encoding="utf-8") as f:
        json.dump({"data": data, "bounds": bounds_json}, f, ensure_ascii=False, indent=2)

    print("\nBounds WGS84:", bounds_json)
    print("Datos guardados en _data.json")


if __name__ == "__main__":
    main()
