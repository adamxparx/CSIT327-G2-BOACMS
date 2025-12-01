import datetime
from django.utils import timezone
from django.db import models
from django.conf import settings
    
class Appointment(models.Model):
    resident = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    CERTIFICATE_TYPE_CHOICES = [
        ('barangay_clearance', 'Barangay Clearance'),
        ('certificate_of_indigency', 'Certificate of Indigency'),
        ('community_tax_certificate', 'Community Tax Certificate'),
        ('solo_parent_certificate', 'Solo Parent Certificate'),
    ]
    certificate_type = models.CharField(max_length=50, choices=CERTIFICATE_TYPE_CHOICES)

    preferred_date = models.DateField()
    preferred_time = models.TimeField()
    purpose = models.CharField(max_length=200, help_text="e.g. Employment, Business Permit, Government Benefits")

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def refresh_if_expired(self):
        preferred_dt = datetime.datetime.combine(self.preferred_date, self.preferred_time)
        preferred_dt = timezone.make_aware(preferred_dt)

        if timezone.is_naive(preferred_dt):
            preferred_dt = timezone.make_aware(preferred_dt)        

        if preferred_dt < timezone.now() and self.status not in ['completed', 'cancelled']:
            self.status = 'cancelled'
            self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.resident.get_full_name()}'s appointment for {self.get_certificate_type_display()} on {self.preferred_date}"

    
    