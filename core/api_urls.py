from django.urls import path

from . import api

app_name = 'api'

urlpatterns = [
    path('', api.index, name='index'),
    path('docs/', api.docs, name='docs'),
    path('salons/', api.salons, name='salons'),
    path('salons/<int:salon_id>/', api.salon_detail, name='salon_detail'),
    path('stats/', api.stats, name='stats'),
]
