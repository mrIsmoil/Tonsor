from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('setup/barber/', views.barber_setup, name='barber_setup'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('barber-portal/', views.barber_entry, name='barber_entry'),
    path('delete-account/confirm/', views.delete_account_confirm, name='delete_account_confirm'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('update-location/', views.update_location, name='update_location'),
    path('set-language/', views.set_language_direct, name='set_language_direct'),
    path('check-email/', views.check_email_exists, name='check_email_exists'),
    path('complete-profile/', views.complete_profile, name='complete_profile'),
]
