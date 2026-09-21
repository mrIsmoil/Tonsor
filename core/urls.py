from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from core.telegram_webhook import telegram_webhook

# Redirect allauth login/signup pages to custom login (signup disabled)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('telegram/webhook/', telegram_webhook, name='telegram_webhook'),
    path('auth/login/', RedirectView.as_view(url='/login/', permanent=False)),
    path('auth/signup/', RedirectView.as_view(url='/login/', permanent=False)),
    path('auth/', include('allauth.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/favicon.ico')),
    path('', include('accounts.urls')),
    path('shops/', include('shops.urls')),
    path('bookings/', include('bookings.urls')),
    path('social/', include('social.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
