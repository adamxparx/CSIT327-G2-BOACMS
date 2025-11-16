from datetime import datetime, time as datetime_time, timedelta

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.generic import TemplateView
from .forms import AppointmentForm
from .models import Appointment
from django.contrib import messages
from django.db import IntegrityError


def find_nearest_available_slot(preferred_date, preferred_time, buffer_minutes=15, max_days=14):
    """Return the nearest future slot (date, time) that is free."""
    open_time = datetime_time(9, 0)
    close_time = datetime_time(16, 30)
    step = timedelta(minutes=15)

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

            conflicts = Appointment.objects.filter(
                preferred_date=current_date,
                preferred_time__range=(slot_start_time, slot_end_time)
            ).exclude(status='cancelled')

            if not conflicts.exists():
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
                appointment.save()
                messages.success(request, "Appointment booked successfully!")
                return redirect('confirmation', appointment_id = appointment.id)
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

    context = {
        'appointments': user_appointments
    }

    return render(request, 'appointments/appointment.html', context)

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
def staff_appointments(request):
    if request.user.role != 'staff':
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')
    
    all_appointments = Appointment.objects.all().order_by('-preferred_date', '-preferred_time')

    if request.method == "POST":
        appointment_id = request.POST.get("appointment_id")
        action = request.POST.get("action")
        appointment = get_object_or_404(Appointment, id=appointment_id)

        status_changed = False

        if action == 'approve':
            if appointment.status == 'cancelled':
                messages.error(request, "Cancelled appointments cannot be approved.")
            elif appointment.status != 'approved':
                appointment.status = 'approved'
                status_changed = True
                messages.success(request, "Appointment approved.")
            else:
                messages.info(request, "Appointment is already approved.")
        elif action == 'decline':
            if appointment.status != 'cancelled':
                appointment.status = 'cancelled'
                status_changed = True
                messages.success(request, "Appointment declined.")
            else:
                messages.info(request, "Appointment is already declined.")
        else:
            messages.error(request, "Invalid action submitted.")
            return redirect('staff_appointments')

        if status_changed:
            appointment.save()

        return redirect('staff_appointments')

    context = {'appointments': all_appointments}
    return render(request, 'appointments/staff_appointment.html', context)

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, resident=request.user)

    if request.method == 'POST':
        appointment.status = 'cancelled'
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
    role = getattr(request.user, 'role')

    if role == 'resident':
        dashboard_template = 'accounts/dashboard.html'
    else:
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
    elif request.user.role == 'staff' or request.user.is_superuser:
        # Staff/Admins can view any
        appointment_qs = Appointment.objects.filter(id=appointment_id)
        template_name = 'appointments/staff_appointment_detail.html' 
    else:
        messages.error(request, "You are not authorized to view this page.")
        return redirect('appointments')

    appointment = get_object_or_404(appointment_qs)
    
    context = {
        'appointment': appointment,
        'certificate_name': appointment.get_certificate_type_display(),
    }

    return render(request, template_name, context)