from django.db import models
from django.conf import settings
from shops.models import BarberProfile, Service
from django.utils.translation import gettext_lazy as _

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('in_progress', _('In Progress')),
        ('canceled', _('Canceled')),
        ('completed', _('Completed')),
        ('no_show', _('Did Not Show')),
    ]
    
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='appointments')
    barber = models.ForeignKey(BarberProfile, on_delete=models.CASCADE, related_name='appointments')
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    employee = models.ForeignKey('shops.Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Tracking fields
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Rating fields
    is_rated = models.BooleanField(default=False)
    rating_is_good = models.BooleanField(null=True, blank=True)
    rating_comment = models.TextField(blank=True)
    
    client_notified = models.BooleanField(default=False)
    
    client_comment = models.TextField(blank=True)
    barber_note = models.TextField(blank=True)
    client_cancel_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.date} {self.time} - {self.client} at {self.barber}"
