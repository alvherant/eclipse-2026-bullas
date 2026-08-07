"""Genera una version 'standalone' del visor: un unico index.html con
todas las imagenes incrustadas en base64 (redimensionadas para pantalla),
sin depender de una carpeta img/ ni de un servidor. Pensado para enviar
por email/WhatsApp/Telegram y abrir con doble clic en PC, Android o
iPhone."""
import base64
import io
import os
import re

from PIL import Image

TRABAJO = r"C:\Users\INGEMISUR\Downloads\Eclipse_Murcia_Bullas\_trabajo"
SITE_DIR = os.path.join(TRABAJO, "site")
IMG_DIR = os.path.join(SITE_DIR, "img")
OUT_PATH = os.path.join(SITE_DIR, "index_standalone.html")

TARGET_WIDTH = 2200  # px, de sobra para cualquier pantalla (incl. retina)


def downscale_to_datauri(png_path, target_width):
    im = Image.open(png_path).convert("RGBA")
    if im.width > target_width:
        ratio = target_width / im.width
        new_size = (target_width, round(im.height * ratio))
        # NEAREST: la mascara solo tiene 3 colores exactos (visible / sombra
        # / transparente); un resample suavizado (Lanczos/bilinear) crea
        # millones de tonos intermedios en los bordes irregulares del
        # relieve y comprime mucho peor que mantener los 3 colores planos.
        im = im.resize(new_size, Image.NEAREST)
    # paleta indexada: al haber solo 3 colores, el PNG resultante es
    # bastante mas pequeno que en RGBA de 32 bits.
    im_p = im.convert("RGBA").quantize(colors=8, method=Image.FASTOCTREE)
    buf = io.BytesIO()
    im_p.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}", len(buf.getvalue())


def main():
    with open(os.path.join(SITE_DIR, "index.html"), encoding="utf-8") as f:
        html = f.read()

    names = sorted(n for n in os.listdir(IMG_DIR) if n.endswith(".png"))
    total_bytes = 0
    for name in names:
        src_path = os.path.join(IMG_DIR, name)
        datauri, nbytes = downscale_to_datauri(src_path, TARGET_WIDTH)
        total_bytes += nbytes
        pattern = f'img/{name}'
        count = html.count(pattern)
        html = html.replace(pattern, datauri)
        print(f"{name}: {os.path.getsize(src_path)/1e6:.1f} MB -> {nbytes/1e6:.1f} MB  ({count} referencia(s) sustituida(s))")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nTotal imagenes embebidas: {total_bytes/1e6:.1f} MB")
    print(f"Archivo final: {OUT_PATH}  ({os.path.getsize(OUT_PATH)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
