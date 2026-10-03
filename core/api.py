"""Tonsor ochiq API — salon ma'lumotlarini o'qish uchun.

Nega bor: saytdan tashqarida ham foydali bo'lishi uchun. Masalan boshqa
dastur "yaqinimdagi sartaroshxonalar" ro'yxatini ko'rsatmoqchi bo'lsa, u
bizning bazamizdan foydalana oladi.

Nega Django REST Framework emas: bu yerda faqat o'qish bor, autentifikatsiya
yo'q, sxema murakkab emas. DRF butun boshli kutubxona — bepul tarifda
xotira va ishga tushish vaqti qimmat turadi. Oddiy JsonResponse yetarli.

XAVFSIZLIK — bu yerda qaytariladigan har bir maydon ochiq internetga
chiqadi. Shuning uchun quyidagilar hech qachon javobga qo'shilmaydi:
  * claim_code — bu kod bilan begona odam salonni "meniki" deb oladi;
  * bank_card_number — to'lov rekvizitlari;
  * foydalanuvchi e'lon qilmagan hamma narsa: email, parol, bronlar,
    mijozlar ro'yxati, telegram_chat_id.
Yangi maydon qo'shayotganda birinchi savol: "buni ko'chada turgan
notanish odam ko'rsa bo'ladimi?" Javob "yo'q" bo'lsa — qo'shilmaydi.
"""

import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET

from core.geo import haversine_km, nearby_box
from shops.models import BarberProfile

# Bitta so'rovda qaytariladigan eng katta ro'yxat. Cheklovsiz bo'lsa
# bitta so'rov butun bazani tortib, bepul tarifdagi CPU limitini yeb
# qo'yishi mumkin.
MAX_LIMIT = 100
DEFAULT_LIMIT = 20

# Masofa bo'yicha qidiruvda hisobga olinadigan eng katta radius.
MAX_RADIUS_KM = 100.0

# Oddiy tezlik chegarasi: bitta IP daqiqasiga shuncha so'rov.
# Haqiqiy foydalanuvchiga xalal bermaydi, lekin sikl ichida so'rov
# yuboradigan skript serverni bo'g'ib qo'ya olmaydi.
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60  # soniya

_rate_state = {}


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        # Birinchisi — haqiqiy mijoz, qolganlari proksilar.
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _rate_limited(request):
    """True — agar shu IP chegaradan oshgan bo'lsa."""
    ip = _client_ip(request)
    if not ip:
        return False

    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    hits = [t for t in _rate_state.get(ip, []) if t > window_start]
    hits.append(now)
    _rate_state[ip] = hits

    # Lug'at cheksiz o'smasligi uchun eskirgan IP'larni tozalab turamiz.
    if len(_rate_state) > 2000:
        for old_ip in [k for k, v in _rate_state.items() if not v or v[-1] < window_start]:
            _rate_state.pop(old_ip, None)

    return len(hits) > RATE_LIMIT_REQUESTS


def _json(data, status=200):
    response = JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})
    # Ma'lumot ochiq va faqat o'qish uchun — boshqa saytdagi brauzer
    # kodi ham chaqira olsin. Yozish uchun endpoint yo'q, shuning uchun
    # bu yerda CSRF xavfi ham yo'q.
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'public, max-age=60'
    return response


def _error(message, status=400):
    return _json({'error': message}, status=status)


def _absolute(request, path):
    return request.build_absolute_uri(path) if path else None


def _int_param(request, name, default, minimum=None, maximum=None):
    """So'rovdagi butun sonni xavfsiz o'qiydi. Noto'g'ri qiymatda — default."""
    raw = request.GET.get(name)
    if raw in (None, ''):
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        value = max(value, minimum)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _float_param(request, name):
    raw = request.GET.get(name)
    if raw in (None, ''):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _salon_brief(profile, request, distance_km=None):
    """Ro'yxat uchun qisqa ko'rinish."""
    data = {
        'id': profile.id,
        'name': profile.shop_name,
        'type': profile.shop_type,
        'address': profile.address or '',
        'rating': round(profile.rating, 2),
        'reviews': profile.good_ratings_count + profile.bad_ratings_count,
        'is_claimed': profile.is_claimed,
        'location': {
            'lat': float(profile.location_lat) if profile.location_lat is not None else None,
            'lng': float(profile.location_lng) if profile.location_lng is not None else None,
        },
        'url': _absolute(request, reverse('shops:barber_profile', args=[profile.id])),
    }
    if distance_km is not None:
        data['distance_km'] = round(distance_km, 2)
    return data


def _salon_full(profile, request):
    """Bitta salon uchun to'liq ko'rinish."""
    data = _salon_brief(profile, request)
    data.update({
        'phone': profile.phone_number or '',
        'instagram': profile.instagram_link or '',
        'telegram': profile.telegram_link or '',
        'currency': profile.currency,
        'hours': {
            'open': profile.open_time.strftime('%H:%M') if profile.open_time else None,
            'close': profile.close_time.strftime('%H:%M') if profile.close_time else None,
            'days': [d for d in profile.work_days.split(',') if d],
        },
        'logo': _absolute(request, profile.logo_url),
        'photos': [
            _absolute(request, image.image.url)
            for image in profile.images.all() if image.image
        ],
        'services': [
            {
                'id': service.id,
                'name': service.name,
                'price': float(service.price),
                'currency': service.currency,
                'duration_minutes': service.duration_minutes,
            }
            for service in profile.services.all()
        ],
        'staff': [
            {
                'name': f'{employee.first_name} {employee.last_name}'.strip(),
                'role': employee.role,
            }
            for employee in profile.employees.all()
        ],
    })
    return data


@require_GET
def index(request):
    """API'ning o'zi haqida — qanday endpoint bor va ular nimani qaytaradi."""
    base = request.build_absolute_uri('/api/')
    return _json({
        'name': 'Tonsor Public API',
        'version': '1',
        'description': "O'zbekistondagi sartaroshxona va go'zallik salonlari "
                       "ma'lumotlari. Faqat o'qish uchun, kalit talab qilinmaydi.",
        'documentation': request.build_absolute_uri(reverse('api:docs')),
        'endpoints': {
            'salons': {
                'url': base + 'salons/',
                'method': 'GET',
                'params': {
                    'q': 'nom yoki manzil bo\'yicha qidiruv',
                    'type': "men yoki women",
                    'lat, lng': 'joylashuv — natija masofa bo\'yicha saralanadi',
                    'radius': f'km, lat/lng bilan birga (eng katta {int(MAX_RADIUS_KM)})',
                    'limit': f'1..{MAX_LIMIT}, standart {DEFAULT_LIMIT}',
                    'offset': 'nechtasini tashlab ketish',
                },
            },
            'salon_detail': {
                'url': base + 'salons/{id}/',
                'method': 'GET',
                'description': "Bitta salon: xizmatlar, ish vaqti, rasmlar.",
            },
            'stats': {
                'url': base + 'stats/',
                'method': 'GET',
                'description': 'Platformadagi umumiy sonlar.',
            },
        },
        'rate_limit': f'{RATE_LIMIT_REQUESTS} so\'rov / {RATE_LIMIT_WINDOW} soniya',
    })


@require_GET
def salons(request):
    """Salonlar ro'yxati — qidiruv, filtr va masofa bo'yicha saralash bilan."""
    if _rate_limited(request):
        return _error("Juda ko'p so'rov. Biroz kutib qayta urinib ko'ring.", status=429)

    queryset = BarberProfile.objects.all()

    query = (request.GET.get('q') or '').strip()
    if query:
        from django.db.models import Q
        queryset = queryset.filter(
            Q(shop_name__icontains=query) | Q(address__icontains=query)
        )

    shop_type = (request.GET.get('type') or '').strip()
    if shop_type in ('men', 'women'):
        queryset = queryset.filter(shop_type=shop_type)

    lat = _float_param(request, 'lat')
    lng = _float_param(request, 'lng')
    limit = _int_param(request, 'limit', DEFAULT_LIMIT, minimum=1, maximum=MAX_LIMIT)
    offset = _int_param(request, 'offset', 0, minimum=0)

    if lat is not None and lng is not None:
        radius = _float_param(request, 'radius') or MAX_RADIUS_KM
        radius = min(max(radius, 0.1), MAX_RADIUS_KM)

        # Avval to'rtburchak bilan kesib olamiz — bu indeksda ishlaydi va
        # keraksiz yozuvlarni Python'ga tortmaydi.
        lat_min, lat_max, lng_min, lng_max = nearby_box(lat, lng, radius)
        nearby = queryset.filter(
            location_lat__isnull=False, location_lng__isnull=False,
            location_lat__gte=lat_min, location_lat__lte=lat_max,
            location_lng__gte=lng_min, location_lng__lte=lng_max,
        )

        measured = []
        for profile in nearby:
            distance = haversine_km(lat, lng, profile.location_lat, profile.location_lng)
            if distance is not None and distance <= radius:
                measured.append((distance, profile))
        measured.sort(key=lambda pair: pair[0])

        total = len(measured)
        page = measured[offset:offset + limit]
        results = [_salon_brief(profile, request, distance) for distance, profile in page]
    else:
        queryset = queryset.order_by('-rating', 'shop_name')
        total = queryset.count()
        results = [
            _salon_brief(profile, request)
            for profile in queryset[offset:offset + limit]
        ]

    return _json({
        'count': total,
        'limit': limit,
        'offset': offset,
        'results': results,
    })


@require_GET
def salon_detail(request, salon_id):
    """Bitta salon haqida to'liq ma'lumot."""
    if _rate_limited(request):
        return _error("Juda ko'p so'rov. Biroz kutib qayta urinib ko'ring.", status=429)

    try:
        profile = (BarberProfile.objects
                   .prefetch_related('services', 'employees', 'images')
                   .get(pk=salon_id))
    except BarberProfile.DoesNotExist:
        return _error('Bunday salon topilmadi.', status=404)

    return _json(_salon_full(profile, request))


@require_GET
def stats(request):
    """Platformadagi umumiy sonlar — ochiq ko'rsatkichlar."""
    if _rate_limited(request):
        return _error("Juda ko'p so'rov. Biroz kutib qayta urinib ko'ring.", status=429)

    from shops.models import Service

    total = BarberProfile.objects.count()
    return _json({
        'salons': total,
        'claimed_salons': BarberProfile.objects.filter(is_claimed=True).count(),
        'salons_with_location': BarberProfile.objects.filter(
            location_lat__isnull=False, location_lng__isnull=False).count(),
        'services': Service.objects.count(),
        'cities': 'Toshkent (birinchi bosqich)',
    })


@require_GET
def docs(request):
    """API hujjati — odam o'qiydigan sahifa."""
    return render(request, 'pages/api.html', {
        'max_limit': MAX_LIMIT,
        'default_limit': DEFAULT_LIMIT,
        'max_radius': int(MAX_RADIUS_KM),
        'rate_limit': RATE_LIMIT_REQUESTS,
        'rate_window': RATE_LIMIT_WINDOW,
    })
