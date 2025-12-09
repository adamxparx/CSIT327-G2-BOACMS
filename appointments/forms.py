from django import forms
from .models import Appointment
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time, timedelta
from django.db import transaction, IntegrityError

class AppointmentForm(forms.ModelForm):
    # Generate time choices in 30-minute intervals from 9:00 AM to 4:30 PM
    TIME_CHOICES = []
    start_time = time(9, 0)   # 9:00 AM
    end_time = time(16, 30)   # 4:30 PM (changed from 5:00 PM)
    
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime('%H:%M')
        time_display = current_time.strftime('%I:%M %p')
        TIME_CHOICES.append((time_str, time_display))
        
        # Add 30 minutes to current time
        hour = current_time.hour
        minute = current_time.minute + 30
        
        if minute >= 60:
            hour += 1
            minute -= 60
            
        current_time = time(hour, minute)
    
    preferred_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        initial='09:00',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Appointment
        fields = ['certificate_type', 'preferred_date', 'preferred_time', 'purpose']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            # 'preferred_time': forms.TimeInput(attrs={'type': 'time'}),  # Removed this line
        }

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get('preferred_date')

        if preferred_date and preferred_date < timezone.now().date() + timedelta(days=1):
            raise ValidationError("You cannot book a date today or in the past.")
        
        return preferred_date
    
    def clean_preferred_time(self):
        preferred_time = self.cleaned_data.get('preferred_time')

        # Convert string time to time object for validation
        if isinstance(preferred_time, str):
            hour, minute = map(int, preferred_time.split(':'))
            preferred_time_obj = time(hour, minute)
        else:
            preferred_time_obj = preferred_time

        open_time = time(9, 0)
        close_time = time(16, 30)  # Changed to 4:30 PM

        if preferred_time_obj and not (open_time <= preferred_time_obj <= close_time):
            raise ValidationError("Appointments are only available between 9:00 AM and 4:30 PM")
        
        return preferred_time
    
    def save(self, commit=True):

        with transaction.atomic():
            instance = super().save(commit=False)

            preferred_date = self.cleaned_data.get('preferred_date')
            preferred_time = self.cleaned_data.get('preferred_time')

            # Convert string time to time object
            if isinstance(preferred_time, str):
                hour, minute = map(int, preferred_time.split(':'))
                preferred_time_obj = time(hour, minute)
            else:
                preferred_time_obj = preferred_time

            buffer_minutes =  30  # Increased buffer to 30 minutes

            start_datetime = timezone.make_aware(
                timezone.datetime.combine(preferred_date, preferred_time_obj)
            )
                
            slot_start = start_datetime - timedelta(minutes=buffer_minutes)
            slot_end = start_datetime + timedelta(minutes=buffer_minutes)

            conflicting_appointments = Appointment.objects.select_for_update().filter(
                preferred_date = preferred_date,
                preferred_time__range = (slot_start.time(), slot_end.time())
            )

            if self.instance and self.instance.pk:
                conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)

            # Allow up to 5 appointments per 30-minute interval
            if conflicting_appointments.count() >= 5:
                raise IntegrityError("Maximum 5 persons can book per 30-minute interval. Please choose a different time.")
                
            return instance