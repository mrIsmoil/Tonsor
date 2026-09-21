import re
import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.uploads import compress_image


def normalize_phone(raw):
    """Telefon raqamini yagona ko'rinishga keltiradi.

    Odamlar raqamni har xil yozadi: "+998 90 111 22 33", "998901112233",
    "90-111-22-33". Bularning hammasi bitta raqam, shuning uchun saqlashdan
    va qidirishdan oldin bo'sh joy va belgilar olib tashlanadi, O'zbekiston
    raqamlari esa to'liq xalqaro ko'rinishga keltiriladi.
    """
    if not raw:
        return ''
    digits = re.sub(r'[^\d]', '', str(raw))
    if not digits:
        return ''
    if len(digits) == 9:            # 901112233 -> operator kodi bilan
        digits = '998' + digits
    elif digits.startswith('8') and len(digits) == 10:   # 8901112233
        digits = '998' + digits[1:]

    # Uzunligi mantiqsiz raqam — yaroqsiz deb qaytariladi. Bu tekshiruvsiz
    # "12" kabi qiymat ham raqam sifatida qabul qilinardi.
    if not 10 <= len(digits) <= 15:
        return ''

    return '+' + digits

class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', _('Male')),
        ('female', _('Female')),
        ('other', _('Other')),
    ]
    
    is_barber = models.BooleanField(_('barber status'), default=False)
    is_client = models.BooleanField(_('client status'), default=False)
    profile_photo = models.ImageField(_('profile photo'), upload_to='profile_photos/', null=True, blank=True)
    gender = models.CharField(_('gender'), max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    age = models.PositiveIntegerField(_('age'), null=True, blank=True)
    latitude = models.DecimalField(_('latitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(_('longitude'), max_digits=9, decimal_places=6, null=True, blank=True)
    is_profile_complete = models.BooleanField(_('profile complete'), default=False)

    # Sartaroshlar o'zini telefon raqami bilan tanishtiradi va ko'pchilikda
    # ishlatadigan email yo'q — shuning uchun telefon kirish uchun asosiy
    # identifikator bo'ladi. Har doim normallashtirilgan holda saqlanadi.
    phone = models.CharField(_('phone'), max_length=20, blank=True, db_index=True)

    # --- Telegram xabarnomalari ---
    # chat_id — xabar yuboriladigan manzil. Bo'sh bo'lsa, foydalanuvchi hali
    # botga ulanmagan: bu xato emas, xabarnoma jimgina o'tkazib yuboriladi.
    telegram_chat_id = models.CharField(
        _('telegram chat id'), max_length=32, blank=True, db_index=True
    )
    # Bir martalik kod: t.me/bot?start=KOD havolasi orqali akkauntni bog'laydi.
    # Bog'langandan keyin tozalanadi, shunda kod qayta ishlatilmaydi.
    telegram_link_code = models.CharField(
        _('telegram link code'), max_length=32, blank=True, db_index=True
    )

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # Yangi yuklangan rasmni saqlashdan oldin kichraytiramiz.
        # update_fields berilganda faqat o'sha maydonlar yoziladi — ro'yxatda
        # rasm bo'lmasa, tegmaymiz (aks holda siqilgan fayl saqlanmay qolardi).
        update_fields = kwargs.get('update_fields')
        if update_fields is None or 'profile_photo' in update_fields:
            compress_image(self.profile_photo)
        super().save(*args, **kwargs)

    def issue_telegram_link_code(self):
        """Yangi bog'lash kodini yaratadi va saqlaydi."""
        self.telegram_link_code = secrets.token_urlsafe(9)
        self.save(update_fields=['telegram_link_code'])
        return self.telegram_link_code
