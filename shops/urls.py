from django.urls import path
from . import views

app_name = 'shops'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('appointment/<int:id>/<str:action>/', views.appointment_action, name='appointment_action'),
    path('profile/<int:barber_id>/', views.barber_profile, name='barber_profile'),
    path('toggle-status/', views.toggle_shop_status, name='toggle_shop_status'),
    path('schedule/', views.today_schedule, name='schedule'),
    path('api/statuses/', views.get_all_shop_statuses, name='api_statuses'),
]
