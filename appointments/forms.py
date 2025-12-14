from django import forms
from .models import Appointment
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
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
        # Format time as 9:00 AM instead of 09:00 AM
        time_display = current_time.strftime('%I:%M %p').lstrip('0')
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
        initial='9:00',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    specify_purpose = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Please specify your purpose',
            'id': 'specify_purpose_input'
        })
    )
    
    class Meta:
        model = Appointment
        fields = ['certificate_type', 'preferred_date', 'preferred_time', 'purpose', 'specify_purpose']
        widgets = {
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'purpose': forms.Select(attrs={'class': 'form-control', 'id': 'purpose_select'}),
            # 'preferred_time': forms.TimeInput(attrs={'type': 'time'}),  # Removed this line
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set purpose to empty string instead of 'employment' default
        self.fields['purpose'].initial = ''

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
    
    def clean(self):
        cleaned_data = super().clean()
        purpose = cleaned_data.get('purpose')
        specify_purpose = cleaned_data.get('specify_purpose')
        
        # If user hasn't selected a purpose (placeholder is still selected)
        if not purpose:
            raise ValidationError({'purpose': 'Please select a purpose.'})
        
        # If user selects 'Others', specify_purpose is required
        if purpose == 'others' and not specify_purpose:
            raise ValidationError({'specify_purpose': 'Please specify your purpose.'})
        
        return cleaned_data
    
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
            
            # Save specify_purpose if 'Others' is selected
            specify_purpose = self.cleaned_data.get('specify_purpose')
            if specify_purpose:
                instance.specify_purpose = specify_purpose
                
            if commit:
                instance.save()
            return instance

class CancellationReasonForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide a reason for cancelling this appointment...',
            'required': True
        }),
        label='Cancellation Reason',
        help_text='Please provide a reason for cancelling this appointment.'
    )

class RescheduleForm(forms.Form):
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'required': True
        }),
        label='New Appointment Date',
        help_text='Select a new date for the appointment.'
    )
    
    # Generate time choices in 30-minute intervals from 9:00 AM to 4:30 PM
    TIME_CHOICES = []
    start_time = datetime.time(9, 0)   # 9:00 AM
    end_time = datetime.time(16, 30)   # 4:30 PM
    
    current_time = start_time
    while current_time <= end_time:
        time_str = current_time.strftime('%H:%M')
        # Format time as 9:00 AM instead of 09:00 AM
        time_display = current_time.strftime('%I:%M %p').lstrip('0')
        TIME_CHOICES.append((time_str, time_display))
        
        # Add 30 minutes to current time
        hour = current_time.hour
        minute = current_time.minute + 30
        
        if minute >= 60:
            hour += 1
            minute -= 60
            
        current_time = datetime.time(hour, minute)
    
    new_time = forms.ChoiceField(
        choices=TIME_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='New Appointment Time',
        help_text='Select a new time for the appointment.'
    )
    
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide a reason for rescheduling this appointment...',
            'required': True
        }),
        label='Reschedule Reason',
        help_text='Please provide a reason for rescheduling this appointment.'
    )
