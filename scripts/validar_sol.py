"""Valida la posicion solar (azimut/altura) para Bullas (Murcia) durante el
eclipse del 12/08/2026, usando efemerides DE421 (skyfield), y localiza el
instante de maxima ocultacion segun luna/sol (aproximado por separacion
angular minima Sol-Luna, como proxy de maxima fase sin libreria de eclipses
dedicada).
"""
from skyfield.api import load, wgs84
from datetime import datetime, timedelta, timezone

BULLAS_LAT = 38.0468805639948700
BULLAS_LON = -1.6677949475113110
BULLAS_ELEV_M = 600  # aproximado, solo afecta refraccion/paralaje minimamente

eph = load('de421.bsp')
ts = load.timescale()

sun = eph['sun']
moon = eph['moon']
earth = eph['earth']
observer = earth + wgs84.latlon(BULLAS_LAT, BULLAS_LON, elevation_m=BULLAS_ELEV_M)

# Ventana: 19:30 a 21:10 hora local (UTC+2 en agosto, CEST), cada minuto
start_local = datetime(2026, 8, 12, 19, 30, tzinfo=timezone(timedelta(hours=2)))
end_local = datetime(2026, 8, 12, 21, 10, tzinfo=timezone(timedelta(hours=2)))

t = start_local
min_sep = 999
min_sep_t = None
print(f"{'Hora local':10s} {'Az sol':>8s} {'Alt sol':>8s} {'Az luna':>8s} {'Alt luna':>8s} {'Separacion':>11s}")
while t <= end_local:
    ts_t = ts.from_datetime(t)
    astrometric_sun = observer.at(ts_t).observe(sun).apparent()
    alt_sun, az_sun, _ = astrometric_sun.altaz()
    astrometric_moon = observer.at(ts_t).observe(moon).apparent()
    alt_moon, az_moon, _ = astrometric_moon.altaz()
    sep = astrometric_sun.separation_from(astrometric_moon).degrees
    if sep < min_sep:
        min_sep = sep
        min_sep_t = t
    if t.minute % 5 == 0:
        print(f"{t.strftime('%H:%M'):10s} {az_sun.degrees:8.2f} {alt_sun.degrees:8.2f} "
              f"{az_moon.degrees:8.2f} {alt_moon.degrees:8.2f} {sep:11.3f}")
    t += timedelta(minutes=1)

print()
print(f"Separacion angular Sol-Luna minima: {min_sep:.3f} grados, a las {min_sep_t.strftime('%H:%M')} hora local")

ts_max = ts.from_datetime(min_sep_t)
alt_sun, az_sun, _ = observer.at(ts_max).observe(sun).apparent().altaz()
print(f"Posicion del sol en ese instante: azimut={az_sun.degrees:.2f} grados, altura={alt_sun.degrees:.2f} grados")

# Puesta de sol aproximada (altura cruza 0, con refraccion estandar -0.833 grados)
t = start_local
prev_alt = None
sunset_t = None
while t <= end_local:
    ts_t = ts.from_datetime(t)
    alt_sun, az_sun, _ = observer.at(ts_t).observe(sun).apparent().altaz()
    if prev_alt is not None and prev_alt >= -0.833 and alt_sun.degrees < -0.833:
        sunset_t = t
        break
    prev_alt = alt_sun.degrees
    t += timedelta(minutes=1)
if sunset_t:
    print(f"Puesta de sol aproximada (altura < -0.833 grados): {sunset_t.strftime('%H:%M')} hora local")
