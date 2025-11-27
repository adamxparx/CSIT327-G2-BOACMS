from django import forms
from .models import Appointment
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time, timedelta
from django.db import transaction, IntegrityError

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['certificate_type', 'preferred_date', 'preferred_time', 'purpose']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'preferred_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get('preferred_date')

        if preferred_date and preferred_date < timezone.now().date() + timedelta(days=1):
            raise ValidationError("You cannot book a date today or in the past.")
        
        return preferred_date
    
    def clean_preferred_time(self):
        preferred_time = self.cleaned_data.get('preferred_time')

        open_time = time(9, 0)
        close_time = time(16, 30)

        if preferred_time and not (open_time <= preferred_time <= close_time):
            raise ValidationError("Appointments are only available between 9:00 AM and 4:30 PM")
        
        return preferred_time
    
    def save(self, commit=True):

        with transaction.atomic():
            instance = super().save(commit=False)

            preferred_date = self.cleaned_data.get('preferred_date')
            preferred_time = self.cleaned_data.get('preferred_time')

            buffer_minutes =  15

            start_datetime = timezone.make_aware(
                timezone.datetime.combine(preferred_date, preferred_time)
            )
                
            slot_start = start_datetime - timedelta(minutes=buffer_minutes)
            slot_end = start_datetime + timedelta(minutes=buffer_minutes)

            conflicting_appointments = Appointment.objects.select_for_update().filter(
                preferred_date = preferred_date,
                preferred_time__range = (slot_start.time(), slot_end.time())
            )

            if self.instance and self.instance.pk:
                conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)

            if conflicting_appointments.exists():
                raise IntegrityError("This slot is too close to an existing appointment. Please choose a different time.")
                
            return instance