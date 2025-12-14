from datetime import datetime, date, time as datetime_time, timedelta
from django.utils import timezone
import datetime as dt

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic import TemplateView
from .forms import AppointmentForm, CancellationReasonForm, RescheduleForm
from .models import Appointment
from django.contrib import messages
from django.db import IntegrityError

from collections import defaultdict

TOTAL_AM_SLOTS = 20
TOTAL_PM_SLOTS = 20



def find_nearest_available_slot(preferred_date, preferred_time, buffer_minutes=30, max_days=14):
    """Return the nearest future slot (date, time) that is free."""
    open_time = datetime_time(8, 0)
    close_time = datetime_time(16, 30)  # Changed to 4:30 PM
    step = timedelta(minutes=30)  # Changed from 15 to 30 minutes
    
    # Convert string time to time object if needed
    if isinstance(preferred_time, str):
        hour, minute = map(int, preferred_time.split(':'))
        preferred_time = datetime_time(hour, minute)

    for day_offset in range(max_days + 1):
        current_date = preferred_date + timedelta(days=day_offset)
        if day_offset == 0:
            candidate_dt = datetime.combine(current_date, preferred_time) + step
        else:
            candidate_dt = datetime.combine(current_date, open_time)

        while candidate_dt.time() <= close_time:
            slot_start_dt = candidate_dt - timedelta(minutes=buffer_minutes)
            slot_end_dt = candidate_dt + timedelta(minutes=buffer_minutes)

            slot_start_time = slot_start_dt.time()
            slot_end_time = slot_end_dt.time()

            if slot_start_dt.date() < current_date:
                slot_start_time = open_time
            if slot_end_dt.date() > current_date:
                slot_end_time = close_time

            # Count appointments in this time slot
            conflicts = Appointment.objects.filter(
                preferred_date=current_date,
                preferred_time__range=(slot_start_time, slot_end_time)
            ).exclude(status='cancelled')

            # Allow up to 5 appointments per 30-minute interval
            if conflicts.count() < 5:
                return {
                    'date': current_date,
                    'time': candidate_dt.time(),
                }

            candidate_dt += step

    return None


@login_required
def create_appointment(request):
    recommended_slot = None

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                appointment = form.save(commit=False)
                appointment.resident = request.user
                appointment.status = 'approved'  # Auto-approve appointments
                
                # Convert string time to time object before saving
                if isinstance(form.cleaned_data['preferred_time'], str):
                    hour, minute = map(int, form.cleaned_data['preferred_time'].split(':'))
                    appointment.preferred_time = datetime_time(hour, minute)
                
                appointment.save()
                messages.success(request, "Appointment booked successfully!")
                return redirect('appointments')
            except IntegrityError:
                form.add_error(None, "This time slot is already taken. Please choose another time.")
                recommended_slot = find_nearest_available_slot(
                    form.cleaned_data['preferred_date'],
                    form.cleaned_data['preferred_time']
                )
                if not recommended_slot:
                    messages.info(request, "All nearby slots are currently full. Please choose another date or time.")
    else:
        initial_data = {}
        for field in ['certificate_type', 'purpose', 'preferred_date', 'preferred_time']:
            value = request.GET.get(field)
            if value:
                initial_data[field] = value

        form = AppointmentForm(initial=initial_data)

    context = {
        'form': form,
        'recommended_slot': recommended_slot,
    }

    return render(request, 'appointments/certification.html', context)


class RequirementsView(TemplateView):
    template_name = 'appointments/requirements.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query_params'] = self.request.GET
        return context

@login_required
def appointments(request):
    user_appointments = Appointment.objects.filter(resident=request.user).order_by('-preferred_date', '-preferred_time')

    claimed_count = user_appointments.filter(status='claimed').count()

    context = {
        'appointments': user_appointments,
        'claimed_count': claimed_count,
    }

    return render(request, 'appointments/appointment.html', context)


@login_required
def claimed_appointments(request):
    appointments = Appointment.objects.filter(resident=request.user).order_by('-preferred_date', '-preferred_time')

    if request.method == 'POST':
        appointment_id = request.POST.get('appointment_id')
        action = request.POST.get('action')
        appointment = get_object_or_404(Appointment, id=appointment_id)
        if action == 'claimed':
            appointment.status = 'completed'
            appointment.save()
            messages.success(request, "Successfully confirmed claimed appointment.")
        else: 
            messages.info(request, "Appointment is already completed")

    context = {
        'appointments': appointments,
    }

    return render(request, 'appointments/claimed_appointments.html', context)

@login_required
def confirmation(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, resident=request.user)

    cert_name = appointment.get_certificate_type_display()

    context = {
        'appointment': appointment,
        'certificate_name': cert_name,
    }

    return render(request, 'appointments/confirmation.html', context)

@login_required
def approved_appointments(request):
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    approved_appointments = Appointment.objects.filter(status__in=['approved', 'claimed'])

    for appt in approved_appointments:
        appt.refresh_if_expired()

    today = dt.date.today()

    approved_appointments = approved_appointments.order_by('preferred_date', 'preferred_time')

    approved_appointments_today = approved_appointments.filter(preferred_date=today).order_by('preferred_time')
    
    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        action = request.POST.get("action")
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if action == 'claimed':
            if appointment.status == 'approved':
                appointment.status = 'claimed'
                appointment.save()
                messages.success(request, "Appointment marked as claimed.")
            else:
                messages.info(request, "Appointment is already marked as claimed.")
        elif action == 'reschedule':
            # Handle reschedule action with new date/time and reason
            reschedule_form = RescheduleForm(request.POST)
            if reschedule_form.is_valid():
                new_date = reschedule_form.cleaned_data['new_date']
                new_time = reschedule_form.cleaned_data['new_time']
                reason = reschedule_form.cleaned_data['reason']
                
                # Convert string time to time object
                if isinstance(new_time, str):
                    hour, minute = map(int, new_time.split(':'))
                    new_time_obj = datetime_time(hour, minute)
                else:
                    new_time_obj = new_time
                
                # Validate the new date/time
                if new_date <= timezone.now().date():
                    messages.error(request, "You cannot reschedule to today or a past date.")
                elif not (datetime_time(9, 0) <= new_time_obj <= datetime_time(16, 30)):
                    messages.error(request, "Appointments are only available between 9:00 AM and 4:30 PM.")
                else:
                    # Check for conflicts (maximum 5 appointments per 30-minute slot)
                    buffer_minutes = 30
                    start_datetime = timezone.make_aware(
                        dt.datetime.combine(new_date, new_time_obj)
                    )
                    slot_start = start_datetime - dt.timedelta(minutes=buffer_minutes)
                    slot_end = start_datetime + dt.timedelta(minutes=buffer_minutes)
                    
                    conflicting_appointments = Appointment.objects.filter(
                        preferred_date=new_date,
                        preferred_time__range=(slot_start.time(), slot_end.time())
                    ).exclude(status='cancelled').exclude(id=appointment.id)
                    
                    if conflicting_appointments.count() >= 5:
                        messages.error(request, "Maximum 5 persons can book per 30-minute interval. Please choose a different time.")
                    else:
                        # Update the appointment with new date/time and reason
                        appointment.preferred_date = new_date
                        appointment.preferred_time = new_time_obj
                        appointment.reschedule_reason = reason
                        appointment.rescheduled_at = timezone.now()
                        appointment.save()
                        messages.success(request, "Appointment rescheduled successfully.")
            else:
                messages.error(request, "Please correct the errors below.")
    
    context = {
        "appointments": approved_appointments,
        "appointments_today": approved_appointments_today,
        "today": today,
    }

    return render(request, "appointments/approved_appointments.html", context)
    
@login_required
def pending_appointments(request):
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    pending_appointments = Appointment.objects.filter(status='pending')

    for appt in pending_appointments:
        appt.refresh_if_expired()
    
    pending_appointments = pending_appointments.order_by('preferred_date', 'preferred_time')

    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        action = request.POST.get("action")  # Get the action (approve or cancel)
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if action == "approve":
            if appointment.status == 'pending':
                appointment.status = 'approved'
                appointment.save()
                messages.success(request, "Appointment approved.")
            else:
                messages.info(request, "Appointment is already approved.")
        elif action == "cancel":
            # Handle cancel action with reason
            if appointment.status == 'pending':
                # Get the cancellation reason from the form
                reason_form = CancellationReasonForm(request.POST)
                if reason_form.is_valid():
                    reason = reason_form.cleaned_data['reason']
                    appointment.status = 'cancelled'
                    appointment.cancellation_reason = reason
                    appointment.save()
                    messages.success(request, "Appointment cancelled successfully.")
                else:
                    # If form is not valid, show error and redisplay the page
                    messages.error(request, "Please provide a valid cancellation reason.")
                    context = {
                        "appointments": pending_appointments,
                        "show_cancel_modal": True,
                        "appointment_to_cancel": appointment.id,
                    }
                    return render(request, "appointments/pending_appointments.html", context)
            else:
                messages.info(request, "Appointment is already cancelled.")

    context = {
        "appointments": pending_appointments,
    }

    return render(request, "appointments/pending_appointments.html", context)

@login_required
def cancelled_appointments(request):
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    cancelled_appointments = Appointment.objects.filter(status='cancelled').order_by('-preferred_date', '-preferred_time')
    
    context = {
        "appointments": cancelled_appointments,
    }

    return render(request, "appointments/cancelled_appointments.html", context)

@login_required
def completed_appointments(request):
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    completed_appointments = Appointment.objects.filter(status='completed').order_by('-preferred_date', '-preferred_time')
    
    context = {
        "appointments": completed_appointments,
    }

    return render(request, "appointments/completed_appointments.html", context)

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, resident=request.user)

    if request.method == 'POST':
        appointment.status = 'cancelled'
        # Automatically set cancellation reason for resident cancellations
        appointment.cancellation_reason = 'Resident cancelled the appointment'
        appointment.save()
        # messages.success(request, 'Appointment has been cancelled successfully.')
        return redirect('appointments')

    context = {'appointment': appointment}
    return render(request, 'appointments/confirm_cancel.html', context)

@login_required
def api_appointments_list(request):
    appointments = Appointment.objects.all() if request.user.role == 'staff' else Appointment.objects.filter(resident=request.user)
        
    data = []
    for appointment in appointments:
        data.append({
            'title': f"{appointment.get_certificate_type_display()} ({appointment.resident.get_full_name()})",
            'start': f"{appointment.preferred_date}T{appointment.preferred_time}",
            'status': appointment.status,
            'url': reverse('appointment_detail', args=[appointment.id]), 
        })
    return JsonResponse(data, safe=False)

@login_required
def appointments_calendar_view(request):
    # Restrict calendar view to staff only
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    dashboard_template = 'accounts/staff_dashboard.html'

    context = {
        'dashboard_template': dashboard_template,
    }

    return render(request, 'appointments/appointments_calendar.html', context)

@login_required
def appointment_detail(request, appointment_id):
    if request.user.role == 'resident':
        # Residents can only view their own
        appointment_qs = Appointment.objects.filter(id=appointment_id, resident=request.user)
        template_name = 'appointments/appointment_detail.html'
        modal_template_name = 'appointments/appointment_detail_modal.html'
    elif request.user.role == 'staff' or request.user.is_superuser:
        # Staff/Admins can view any
        appointment_qs = Appointment.objects.filter(id=appointment_id)
        template_name = 'appointments/staff_appointment_detail.html'
        modal_template_name = 'appointments/staff_appointment_detail_modal.html'
    else:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')

    appointment = get_object_or_404(appointment_qs)
    
    context = {
        'appointment': appointment,
        'certificate_name': appointment.get_certificate_type_display(),
    }
    
    # Check if this is an AJAX request for modal content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return only the modal content, not the full page
        return render(request, modal_template_name, context)
    
    # For regular requests, return the full page
    return render(request, template_name, context)

@login_required
def api_month_availability(request):
    booked = defaultdict(lambda: {"am": 0, "pm": 0})

    for appt in Appointment.objects.all():
        period = "am" if appt.preferred_time.hour < 12 else "pm"
        booked[str(appt.preferred_date)]["am" if period=="am" else "pm"] += 1

    # Current month
    today = date.today()
    first_day = today.replace(day=1)
    if first_day.month == 12:
        next_month = first_day.replace(year=first_day.year+1, month=1, day=1)
    else:
        next_month = first_day.replace(month=first_day.month+1, day=1)

    days_in_month = (next_month - first_day).days

    response = []
    for i in range(days_in_month):
        d = first_day + timedelta(days=i)
        counts = booked.get(str(d), {"am": 0, "pm": 0})
        response.append({
            "date": str(d),
            "am": max(TOTAL_AM_SLOTS - counts["am"], 0),
            "pm": max(TOTAL_PM_SLOTS - counts["pm"], 0),
        })

    return JsonResponse(response, safe=False)


@login_required
def api_date_availability(request):
    """Get slot availability for a specific date"""
    date_str = request.GET.get('date')
    
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Count appointments for AM (before 12:00 PM) and PM (12:00 PM and after)
    appointments = Appointment.objects.filter(
        preferred_date=selected_date
    ).exclude(status='cancelled')
    
    am_count = appointments.filter(preferred_time__lt=datetime_time(12, 0)).count()
    pm_count = appointments.filter(preferred_time__gte=datetime_time(12, 0)).count()
    
    # Total slots per session (max 30 per session)
    TOTAL_SLOTS = 30
    
    response = {
        'date': date_str,
        'am_available': max(TOTAL_SLOTS - am_count, 0),
        'pm_available': max(TOTAL_SLOTS - pm_count, 0),
        'am_booked': am_count,
        'pm_booked': pm_count
    }
    
    return JsonResponse(response)