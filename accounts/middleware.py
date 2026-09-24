from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from core.uploads import human_mb, limit_for


class UploadLimitMiddleware:
    """Haddan tashqari katta fayllarni view'ga yetib bormasdan to'xtatadi.

    Saytda fayl yuklaydigan ettita joy bor va ularning birortasida hajm
    tekshiruvi yo'q edi — ya'ni bitta foydalanuvchi yuz megabaytlik fayl
    tashlab diskni to'ldirib qo'yishi mumkin edi. Tekshiruvni har bir
    view'ga ko'chirib yurgandan ko'ra, shu yerda bir marta qilgan
    ma'qul: kelajakda qo'shiladigan yangi yuklash sahifalari ham
    avtomatik himoyalangan bo'ladi.

    Foydalanuvchi xatoni oddiy til bilan ko'radi va o'zi turgan sahifaga
    qaytariladi — hech narsa yo'qolmaydi, boshqa rasm tanlashi kifoya.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST' and request.content_type and \
                request.content_type.startswith('multipart/form-data'):
            too_big = self._find_oversized(request)
            if too_big is not None:
                field, size, limit = too_big
                messages.error(
                    request,
                    f'Fayl juda katta ({human_mb(size)}). '
                    f'Ruxsat etilgan eng katta hajm — {human_mb(limit)}.'
                )
                return redirect(request.get_full_path())
        return self.get_response(request)

    def _find_oversized(self, request):
        try:
            files = request.FILES
        except Exception:
            # Buzuq yoki yarim uzilgan so'rov — buni view yoki Django o'zi
            # hal qiladi, biz aralashmaymiz.
            return None

        # .lists() — chunki bitta maydon nomi ostida bir nechta fayl
        # kelishi mumkin; .items() ulardan faqat oxirgisini qaytaradi.
        for field, uploaded_list in files.lists():
            limit = limit_for(field)
            for uploaded in uploaded_list:
                size = getattr(uploaded, 'size', 0) or 0
                if size > limit:
                    return field, size, limit
        return None


class CanonicalHostMiddleware:
    """Google's registered OAuth redirect URI is pinned to the Sites-framework domain
    (127.0.0.1:8000). Django happily serves the same dev server on 'localhost:8000' too
    (both are in ALLOWED_HOSTS), but allauth builds the redirect_uri from whatever host the
    browser actually used — so a visit via 'localhost' produces an unregistered redirect_uri
    and Google rejects it with redirect_uri_mismatch. Canonicalize to 127.0.0.1 up front so
    the two hostnames can never diverge for the user.
    """
    CANONICAL_HOST = '127.0.0.1'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        hostname = host.split(':')[0]
        if hostname == 'localhost':
            canonical_host = host.replace('localhost', self.CANONICAL_HOST, 1)
            return redirect(f'{request.scheme}://{canonical_host}{request.get_full_path()}')
        return self.get_response(request)


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
            
            # Xodimlar (is_staff) mijoz emas: ular platformani boshqaradi.
            # Ularni mijoz profilini to'ldirishga majburlash salon qo'shish
            # sahifasini ham yopib qo'yardi — `createsuperuser` bilan ochilgan
            # hisobda is_profile_complete har doim False bo'ladi.
            if (not request.user.is_profile_complete
                    and portal_type == 'client'
                    and not request.user.is_barber
                    and not request.user.is_staff):
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

                is_set_language = False
                try: is_set_language = path == reverse('accounts:set_language_direct')
                except: is_set_language = 'set-language' in path

                # If not on an allowed path, redirect to completion page
                if not any([is_auth_process, is_static_or_media, is_admin, is_complete_profile, is_logout, is_set_language]):
                    return redirect('accounts:complete_profile')

        return self.get_response(request)
