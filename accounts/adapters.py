from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Google bilan kirishda email to'qnashuvini hal qiladi.

        Muammo: agar Google qaytargan pochta bilan saytda allaqachon hisob
        bo'lsa, allauth avtomatik ro'yxatdan o'tkaza olmaydi va o'zining
        bezaksiz "Sign Up" sahifasini ko'rsatadi. Foydalanuvchi uchun bu
        buzilgan sayt bo'lib ko'rinadi.

        Nega avtomatik ulab qo'ymaymiz: saytda pochta tasdiqlanmaydi
        (ACCOUNT_EMAIL_VERIFICATION = 'none'). Ya'ni kimdir boshqa odamning
        pochtasi bilan sartarosh hisobini ochishi mumkin. Keyin pochtaning
        haqiqiy egasi Google orqali kirsa va biz uni avtomatik ulasak, u
        begona hisobga tushib qolardi — paroli esa o'sha birinchi odamda.
        Shuning uchun ulash emas, aniq tushuntirish beramiz.
        """
        # Bu Google hisobi allaqachon bog'langan — oddiy kirish, tegmaymiz.
        if sociallogin.is_existing:
            return

        email = (sociallogin.user.email or '').strip()
        if not email:
            return

        User = get_user_model()
        if not User.objects.filter(email__iexact=email).exists():
            return  # Yangi foydalanuvchi — avtomatik ro'yxatdan o'tadi.

        messages.error(
            request,
            f'{email} pochtasi bilan hisob allaqachon mavjud. '
            'Parolingiz bilan kiring.'
        )
        raise ImmediateHttpResponse(redirect(reverse('accounts:login')))

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
