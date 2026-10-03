from django.urls import path

from . import pages

app_name = 'pages'

urlpatterns = [
    path('loyiha/', pages.project, name='project'),
    path('demo/', pages.demo, name='demo'),
]
