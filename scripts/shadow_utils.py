"""Calculo de sombra de terreno (oclusion de horizonte) para una direccion
solar dada (azimut/altura), sobre una malla de elevaciones (numpy array).

Metodo: rota la malla para alinear la direccion del sol con el eje de filas,
luego hace un barrido acumulando el maximo de f(s) = z - s*tan(altura) desde
el lado del sol hacia el lado opuesto; una celda esta en sombra si algun
punto mas cercano al sol proyecta una altura efectiva mayor que la suya.
"""
import numpy as np
from scipy.ndimage import rotate as ndi_rotate


def compute_shadow_mask(elev, pixel_size, azimuth_deg, altitude_deg, fill_value=-9999.0):
    """
    elev: array 2D (row=north->south creciente, col=west->east creciente)
    pixel_size: tamaño de pixel en metros
    azimuth_deg: direccion HACIA el sol, 0=Norte, 90=Este, 180=Sur, 270=Oeste
    altitude_deg: altura solar en grados sobre el horizonte
    Devuelve: array booleano mismo shape que elev. True = en sombra (sol oculto).
    """
    if altitude_deg <= 0:
        # sol bajo el horizonte: todo en sombra
        return np.ones_like(elev, dtype=bool)

    h, w = elev.shape
    diag = int(np.ceil(np.hypot(h, w))) + 4
    pad_h = (diag - h) // 2 + 2
    pad_w = (diag - w) // 2 + 2
    padded = np.pad(elev, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant",
                     constant_values=fill_value)

    # queremos que, tras rotar, la direccion HACIA el sol quede alineada con
    # fila decreciente (arriba de la imagen). En la imagen original, fila
    # decreciente = Norte, fila creciente = Sur; columna creciente = Este.
    # azimuth 0=Norte ya esta alineado con "arriba"; para alinear una
    # direccion arbitraria con "arriba" hay que rotar la imagen -azimuth
    # (en el sentido de scipy, validado empiricamente en test unitario).
    rotated = ndi_rotate(padded, angle=azimuth_deg, reshape=False, order=0,
                          cval=fill_value, prefilter=False)

    rows = np.arange(rotated.shape[0]).reshape(-1, 1) * pixel_size
    # fila 0 = lado del sol (mas cerca), s crece hacia abajo (alejandose del sol).
    # g(s) = z(s) + s*tan(altura): un punto aguas abajo (mayor s) esta en
    # sombra si algun punto mas cercano al sol (menor s) tiene g mayor.
    g = rotated + rows * np.tan(np.radians(altitude_deg))
    running_max = np.maximum.accumulate(g, axis=0)
    # excluir la propia fila del maximo acumulado (sombra = superada por algo
    # estrictamente anterior, no por si misma)
    running_max_prev = np.vstack([
        np.full((1, g.shape[1]), -np.inf, dtype=g.dtype),
        running_max[:-1],
    ])
    shadow_rot = running_max_prev > g

    # las celdas de relleno (fuera del DEM original) no deben considerarse
    # sombra real; las descartamos tras des-rotar via una mascara de validez
    valid_rot = rotated > (fill_value + 1)

    shadow_back = ndi_rotate(shadow_rot.astype(np.float32), angle=-azimuth_deg,
                              reshape=False, order=0, cval=0.0, prefilter=False)
    valid_back = ndi_rotate(valid_rot.astype(np.float32), angle=-azimuth_deg,
                             reshape=False, order=0, cval=0.0, prefilter=False)

    shadow_crop = shadow_back[pad_h:pad_h + h, pad_w:pad_w + w]
    valid_crop = valid_back[pad_h:pad_h + h, pad_w:pad_w + w]

    shadow_mask = (shadow_crop > 0.5) & (valid_crop > 0.5)
    return shadow_mask


if __name__ == "__main__":
    # Test unitario: pico de altura 10 en el centro de una malla plana,
    # sol al oeste (azimut=270) y altura 45 grados -> el pico debe proyectar
    # sombra hacia el ESTE (columnas mayores), longitud ~10 px (tan(45)=1).
    n = 41
    z = np.zeros((n, n), dtype=np.float32)
    cy, cx = n // 2, n // 2
    z[cy, cx] = 10.0

    mask = compute_shadow_mask(z, pixel_size=1.0, azimuth_deg=270, altitude_deg=45)
    fila = mask[cy, cx:cx + 15].astype(int)
    print("Fila central desde el pico hacia el ESTE (deberia haber ~10 True tras el pico):")
    print(fila)

    fila_oeste = mask[cy, cx - 15:cx].astype(int)
    print("Fila central desde el OESTE hacia el pico (deberia ser todo False, el sol viene de ahi):")
    print(fila_oeste)
