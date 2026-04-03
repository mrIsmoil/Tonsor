from django.shortcuts import redirect
from django.urls import reverse

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Track portal preference from query parameters or path
        portal_param = request.GET.get('portal')
        if portal_param in ['client', 'business']:
            request.session['portal_type'] = portal_param
        elif request.path.startswith('/barber-entry/') or request.path.startswith('/shops/dashboard/'):
            request.session['portal_type'] = 'business'

        if request.user.is_authenticated:
            # 2. Determine if we should enforce profile completion
            # Default to 'client' if not specified, but EXEMPT barbers
            portal_type = request.session.get('portal_type', 'client')
            
            if not request.user.is_profile_complete and portal_type == 'client' and not request.user.is_barber:
                path = request.path
                
                # Allowed paths: completion page, logout, admin, social account callbacks, static/media
                is_auth_process = path.startswith('/auth/')
                is_static_or_media = path.startswith('/static/') or path.startswith('/media/')
                is_admin = path.startswith('/admin/')
                
                is_complete_profile = False
                try: is_complete_profile = path == reverse('accounts:complete_profile')
                except: is_complete_profile = 'complete-profile' in path
                
                is_logout = False
                try: is_logout = path == reverse('account_logout')
                except: is_logout = 'logout' in path
                
                # If not on an allowed path, redirect to completion page
                if not any([is_auth_process, is_static_or_media, is_admin, is_complete_profile, is_logout]):
                    return redirect('accounts:complete_profile')

        return self.get_response(request)
