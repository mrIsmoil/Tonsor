from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('client/', views.client_home, name='client_home'),
    path('book/<int:barber_id>/', views.book_appointment, name='book_appointment'),
    path('search/', views.search_barbers, name='search_barbers'),
    path('notify/read/', views.mark_notification_read, name='mark_notification_read'),
    path('cancel/<int:id>/', views.cancel_appointment, name='cancel_appointment'),
    path('rate/<int:id>/', views.rate_appointment, name='rate_appointment'),
    path('my-appointments/', views.my_appointments, name='my_appointments'),
]
