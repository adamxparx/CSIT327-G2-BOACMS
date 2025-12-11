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
        ('claimed', 'Claimed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Add cancellation reason field
    cancellation_reason = models.TextField(blank=True, null=True, help_text="Reason for cancellation provided by staff")

    # Add reschedule reason field
    reschedule_reason = models.TextField(blank=True, null=True, help_text="Reason for rescheduling provided by staff")
    
    # Add rescheduled timestamp
    rescheduled_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when the appointment was rescheduled")

    created_at = models.DateTimeField(auto_now_add=True)

    def refresh_if_expired(self):    
        if self.preferred_date < timezone.localdate() and self.status not in ['completed', 'cancelled', 'claimed']:
            self.status = 'cancelled'
            self.save(update_fields=['status'])

    def __str__(self):
        return f"{self.resident.get_full_name()}'s appointment for {self.get_certificate_type_display()} on {self.preferred_date}"