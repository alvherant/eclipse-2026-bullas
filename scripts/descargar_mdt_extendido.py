"""Descarga el MDT05 (IGN WCS, Elevacion25830_5) para el area extendida
Cehegin + Bullas + Mula + Pliego, en mosaico de teselas (el servidor limita
a 4096 px por eje), y las fusiona en un unico GeoTIFF."""
from osgeo import gdal

import math
import os
import urllib.request

gdal.UseExceptions()

BASE = r"C:\Users\INGEMISUR\Downloads\Eclipse_Murcia_Bullas"
TILES_DIR = os.path.join(BASE, "_mdt_tiles")
OUT = os.path.join(BASE, "MDT05_extendido.tif")
os.makedirs(TILES_DIR, exist_ok=True)

# bbox que cubre los 4 terminos municipales (calculado desde
# recintos_municipales_inspire_peninbal_etrs89, filtrado por
# Cehegin/Bullas/Mula/Pliego, reproyectado a ETRS89/UTM30N), con margen
# redondeado a multiplos de 5 m.
MINX, MAXX = 602000, 644500
MINY, MAXY = 4191000, 4228000

TILE_M = 18000  # 3600 px a 5 m/px, bajo el limite MAXSIZE=4096 del WCS
PIXEL = 5

WCS_URL = "https://servicios.idee.es/wcs-inspire/mdt"


def tile_bounds():
    nx = math.ceil((MAXX - MINX) / TILE_M)
    ny = math.ceil((MAXY - MINY) / TILE_M)
    tiles = []
    for j in range(ny):
        for i in range(nx):
            tx0 = MINX + i * TILE_M
            tx1 = min(tx0 + TILE_M, MAXX)
            ty0 = MINY + j * TILE_M
            ty1 = min(ty0 + TILE_M, MAXY)
            tiles.append((tx0, ty0, tx1, ty1))
    return tiles


def descargar_tesela(tx0, ty0, tx1, ty1, out_path):
    url = (
        f"{WCS_URL}?service=WCS&version=2.0.1&request=GetCoverage"
        f"&CoverageId=Elevacion25830_5&subset=x({tx0},{tx1})&subset=y({ty0},{ty1})"
        "&format=image/tiff"
    )
    with urllib.request.urlopen(url, timeout=300) as r:
        data = r.read()
    with open(out_path, "wb") as f:
        f.write(data)


def main():
    tiles = tile_bounds()
    print(f"Descargando {len(tiles)} teselas de {TILE_M}m ({TILE_M//PIXEL}px)...")
    tile_paths = []
    for k, (tx0, ty0, tx1, ty1) in enumerate(tiles):
        out_path = os.path.join(TILES_DIR, f"tile_{k:02d}.tif")
        tile_paths.append(out_path)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  [{k+1}/{len(tiles)}] {tx0},{ty0} -> {tx1},{ty1}  (ya existe, se omite)")
            continue
        print(f"  [{k+1}/{len(tiles)}] {tx0},{ty0} -> {tx1},{ty1} ...", flush=True)
        descargar_tesela(tx0, ty0, tx1, ty1, out_path)
        sz = os.path.getsize(out_path)
        print(f"      OK {sz/1e6:.1f} MB")

    print("Fusionando teselas...")
    vrt_path = os.path.join(TILES_DIR, "_mosaico.vrt")
    gdal.BuildVRT(vrt_path, tile_paths)
    gdal.Translate(OUT, vrt_path, format="GTiff",
                    creationOptions=["COMPRESS=DEFLATE", "PREDICTOR=2", "TILED=YES"])
    print("Guardado:", OUT)

    ds = gdal.Open(OUT)
    print("Tamano final:", ds.RasterXSize, "x", ds.RasterYSize, "px")
    print("GeoTransform:", ds.GetGeoTransform())


if __name__ == "__main__":
    main()
