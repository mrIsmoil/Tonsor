from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.uploads import compress_image

class BarberProfile(models.Model):
    # Egasi bo'lmagan profil ham mavjud bo'la oladi: sartaroshxonani biz o'zimiz
    # ochiq manbalardan (2GIS, xarita) kiritamiz, sartarosh keyinroq uni
    # "o'ziniki" deb tasdiqlab oladi. Shu paytgacha user bo'sh turadi.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='barber_profile', null=True, blank=True,
    )
    # Egasi tasdiqlaganmi. Faqat tasdiqlangan profil bron qabul qiladi —
    # sartarosh bilmagan bronni mijozga va'da qilib bo'lmaydi.
    is_claimed = models.BooleanField(_('claimed by owner'), default=True)
    # Sartaroshga beriladigan kod: u shu kod bilan profilni o'ziniki qiladi.
    claim_code = models.CharField(_('claim code'), max_length=16, blank=True, db_index=True)
    # Ochiq manbadan olingan telefon — sartarosh bilan bog'lanish uchun.
    contact_phone = models.CharField(_('contact phone'), max_length=32, blank=True)

    shop_name = models.CharField(_('shop name'), max_length=255)
    location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address = models.TextField(_('address'), blank=True)
    SHOP_TYPE_CHOICES = [
        ('men', _("Men's Barber")),
        ('women', _("Women's Salon")),
    ]
    shop_type = models.CharField(_('shop type'), max_length=20, choices=SHOP_TYPE_CHOICES, default='men')
    CURRENCY_CHOICES = [
        ('UZS', 'UZS'),
        ('USD', 'USD'),
    ]
    currency = models.CharField(_('currency'), max_length=3, choices=CURRENCY_CHOICES, default='UZS')
    
    # Working details
    open_time = models.TimeField(_('opening time'), null=True, blank=True)
    close_time = models.TimeField(_('closing time'), null=True, blank=True)
    work_days = models.CharField(_('work days'), max_length=100, default='Mon,Tue,Wed,Thu,Fri,Sat,Sun')
    depends_on_owner = models.BooleanField(default=False)
    is_open_now = models.BooleanField(_('is open now'), default=False)
    
    # Rating System
    rating = models.FloatField(_('rating'), default=0.0)
    good_ratings_count = models.PositiveIntegerField(default=0)
    bad_ratings_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def is_new(self):
        from datetime import timedelta
        return timezone.now() - self.created_at < timedelta(days=1)
    
    # Contact
    phone_number = models.CharField(max_length=20, blank=True)
    instagram_link = models.URLField(blank=True)
    telegram_link = models.URLField(blank=True)
    
    # Payment
    bank_card_number = models.CharField(max_length=16, blank=True)
    
    @property
    def logo_url(self):
        logo = self.images.filter(is_logo=True).first()
        if logo:
            return logo.image.url
        # Egasiz profilda user yo'q — bunda logotip ham bo'lmaydi.
        if self.user and self.user.profile_photo:
            return self.user.profile_photo.url
        return None

    def generate_claim_code(self):
        """Sartaroshga beriladigan qisqa kod: TNS-4821 ko'rinishida.

        Qo'lda o'qib, telefonda terish uchun qulay bo'lishi kerak — shuning
        uchun qisqa va faqat raqamdan iborat.
        """
        import random
        while True:
            code = f"TNS-{random.randint(1000, 9999)}"
            if not BarberProfile.objects.filter(claim_code=code).exists():
                self.claim_code = code
                self.save(update_fields=['claim_code'])
                return code
    
    @property
    def min_price(self):
        from django.db.models import Min
        return self.services.aggregate(Min('price'))['price__min']

    @property
    def short_address(self):
        if not self.address:
            return ""
        parts = [p.strip() for p in self.address.split(',')]
        if len(parts) >= 5:
            # Uzbekistan (0), Ferghana (1), Kokand (2), Settlement (3), Street (4) -> Country, City, Street
            return f"{parts[0]}, {parts[2]}, {parts[4]}"
        elif len(parts) >= 3:
            # Country, City
            return f"{parts[0]}, {parts[2]}"
        return self.address

    def __str__(self):
        return self.shop_name

class ShopImage(models.Model):
    profile = models.ForeignKey(BarberProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='shop_images/')
    is_logo = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        compress_image(self.image)
        super().save(*args, **kwargs)

class Employee(models.Model):
    ROLE_CHOICES = [
        ('professional', _('Professional')),
        ('apprentice', _('Apprentice')),
    ]
    profile = models.ForeignKey(BarberProfile, on_delete=models.CASCADE, related_name='employees')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='professional')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Service(models.Model):
    profile = models.ForeignKey(BarberProfile, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='service_images/', blank=True, null=True)
    CURRENCY_CHOICES = [
        ('UZS', 'UZS'),
        ('USD', 'USD'),
    ]
    price = models.DecimalField(_('price'), max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS')
    duration_minutes = models.PositiveIntegerField(default=30)

    def save(self, *args, **kwargs):
        compress_image(self.image)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.price} UZS"


class ShopInvite(models.Model):
    """Mijozning "bu sartaroshni Tonsorga taklif qiling" so'rovi.

    Oddiy hisoblagich o'rniga alohida yozuv saqlanadi, chunki sotuvda
    "7 marta bosilgan" emas, "7 xil odam so'ragan" degan dalil kerak.
    Har bir mijoz bitta salon uchun faqat bir marta hisoblanadi.
    """
    shop = models.ForeignKey(
        BarberProfile, on_delete=models.CASCADE, related_name='invites'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_invites'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Bitta mijoz bitta salonni ikki marta so'ray olmaydi.
        unique_together = ('shop', 'client')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client} -> {self.shop}"
