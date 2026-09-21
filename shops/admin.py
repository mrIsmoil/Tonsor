from django.contrib import admin
from .models import BarberProfile, ShopImage, Employee, Service

admin.site.register(BarberProfile)
admin.site.register(ShopImage)
admin.site.register(Employee)
admin.site.register(Service)
