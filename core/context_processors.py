from django.conf import settings

def map_api_key(request):
    return {
        'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', '')
    }
