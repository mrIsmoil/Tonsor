from django.contrib import admin
from django.utils.html import format_html

from .models import BarberProfile, Employee, Service, ShopImage, ShopInvite


@admin.register(BarberProfile)
class BarberProfileAdmin(admin.ModelAdmin):
    """Dala ishi uchun ro'yxat.

    Salonlar ko'chada yig'iladi, keyin ularga qayta borish kerak bo'ladi.
    Standart ko'rinishda faqat nom chiqardi — telefon, claim kodi va kim
    qabul qilgani ko'rinmasdi, ya'ni ro'yxat amalda foydasiz edi.
    """

    list_display = ('shop_name', 'shop_type', 'contact_phone', 'claim_code_col',
                    'claimed_col', 'invites_col', 'has_location', 'created_at')
    list_filter = ('is_claimed', 'shop_type', 'created_at')
    search_fields = ('shop_name', 'contact_phone', 'address', 'claim_code')
    ordering = ('-created_at',)
    list_per_page = 50
    readonly_fields = ('created_at',)

    @admin.display(description='Claim kodi', ordering='claim_code')
    def claim_code_col(self, obj):
        if not obj.claim_code:
            return '—'
        # Kod ko'chada ovoz chiqarib o'qiladi, shuning uchun ajralib tursin.
        return format_html('<code style="font-size:13px">{}</code>', obj.claim_code)

    @admin.display(description='Qabul qilingan', boolean=True, ordering='is_claimed')
    def claimed_col(self, obj):
        return obj.is_claimed

    @admin.display(description='So\' raganlar')
    def invites_col(self, obj):
        """Nechta mijoz "shu salon kerak" degan.

        Sartaroshga ikkinchi marta borganda asosiy dalil shu raqam.
        """
        n = obj.invites.count()
        return n or '—'

    @admin.display(description='Xarita', boolean=True)
    def has_location(self, obj):
        return obj.location_lat is not None and obj.location_lng is not None

    def get_queryset(self, request):
        # Har qator uchun alohida so'rov ketmasligi uchun.
        return super().get_queryset(request).prefetch_related('invites')


@admin.register(ShopInvite)
class ShopInviteAdmin(admin.ModelAdmin):
    list_display = ('shop', 'client', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('shop__shop_name', 'client__username')
    ordering = ('-created_at',)


admin.site.register(ShopImage)
admin.site.register(Employee)
admin.site.register(Service)
