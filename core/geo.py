"""Joylashuv bo'yicha masofa hisoblash.

SQLite'da geografik funksiyalar yo'q, PostGIS esa bu bosqichda ortiqcha
murakkablik. Salonlar soni hozircha minglab emas, shuning uchun masofani
Python'da hisoblash butunlay yetarli: 1000 ta salon uchun ~10 millisekund.

Baza kattalashganda birinchi qadam — `nearby_box()` bilan kerakli
to'rtburchakni kesib olish (u indekslangan ustunlarda ishlaydi), keyin
faqat qolganlari uchun aniq masofa hisoblash.
"""

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1, lng1, lat2, lng2):
    """Ikki nuqta orasidagi masofa (km). Noto'g'ri qiymatda None."""
    try:
        lat1, lng1 = float(lat1), float(lng1)
        lat2, lng2 = float(lat2), float(lng2)
    except (TypeError, ValueError):
        return None

    d_lat = radians(lat2 - lat1)
    d_lng = radians(lng2 - lng1)
    a = (sin(d_lat / 2) ** 2
         + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lng / 2) ** 2)
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def nearby_box(lat, lng, radius_km):
    """Radiusni qamrab oluvchi to'rtburchak: (lat_min, lat_max, lng_min, lng_max).

    Bazadan ortiqcha yozuv tortmaslik uchun oldindan filtr sifatida
    ishlatiladi. Chekkalarda radiusdan bir oz kattaroq hudud tushadi —
    aniq masofa keyin haversine bilan tekshiriladi.
    """
    lat = float(lat)
    lng = float(lng)
    d_lat = radius_km / 111.0
    # Qutbga yaqinlashgan sari meridianlar yaqinlashadi, shuning uchun
    # uzunlik darajasi kengligi kenglikka bog'liq.
    cos_lat = max(cos(radians(lat)), 0.01)
    d_lng = radius_km / (111.0 * cos_lat)
    return lat - d_lat, lat + d_lat, lng - d_lng, lng + d_lng


def format_distance(km, lang='uz'):
    """Masofani odam o'qiydigan ko'rinishga keltiradi."""
    if km is None:
        return ''
    units = {
        'uz': ('m', 'km'),
        'ru': ('м', 'км'),
        'en': ('m', 'km'),
    }.get(lang, ('m', 'km'))

    if km < 1:
        return f'{int(round(km * 1000 / 10) * 10)} {units[0]}'
    if km < 10:
        return f'{km:.1f} {units[1]}'
    return f'{int(round(km))} {units[1]}'


def parse_coords(lat_raw, lng_raw):
    """Matn ko'rinishidagi koordinatalarni tekshirib qaytaradi.

    Foydalanuvchi manzil qatoriga istalgan narsa yozishi mumkin, shuning
    uchun diapazon ham tekshiriladi — aks holda xarita dunyoning narigi
    chetiga sakrab ketardi.
    """
    try:
        lat = float(lat_raw)
        lng = float(lng_raw)
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None
    return lat, lng
