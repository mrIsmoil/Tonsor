from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.shortcuts import redirect

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        # If the user has not completed their profile, redirect to complete_profile
        if hasattr(user, 'is_profile_complete') and not user.is_profile_complete:
            return reverse('accounts:complete_profile')
        
        # Default behavior: check if user is barber/client and redirect
        if user.is_barber:
            return reverse('shops:dashboard')
        elif user.is_client:
            return reverse('bookings:client_home')
        
        return super().get_login_redirect_url(request)
