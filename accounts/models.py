from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

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

    def __str__(self):
        return self.username
