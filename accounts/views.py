from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from .forms import CustomUserCreationForm, CustomUserUpdateForm, ResidentForm
from appointments.models import Appointment
from django.contrib.auth import get_user_model
import datetime

def auth_check(user):
    if user.is_authenticated:
        if user.role == 'resident':
            return redirect('dashboard')
        elif user.role == 'staff':
            return redirect('staff_dashboard')
    return None

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    def dispatch(self, request, *args, **kwargs):
        response = auth_check(request.user)
        if response:
            return response
        return super().dispatch(request, *args, **kwargs)
      
def index(request):
    user = request.user
    response = auth_check(user)
    if response:
        return response
    
    context = {
        'user': user,
    }
    return render(request, 'accounts/index.html', context)

def register(request):
    response = auth_check(request.user)
    if response:
        return response
    
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        resident_form = ResidentForm(request.POST)
        if user_form.is_valid() and resident_form.is_valid():
            user = user_form.save()
            resident = resident_form.save(commit=False)
            resident.user = user
            resident.save()
            messages.success(request, 'Your account has been created successfully!')
            return redirect('login') 
    else:
        user_form = CustomUserCreationForm()
        resident_form = ResidentForm()

    context = {
        'user_form': user_form,
        'resident_form': resident_form,
    }
    return render(request, 'accounts/register.html', context)

@login_required
def dashboard(request):
    user = request.user

    if user.role == 'staff':
        return redirect('staff_dashboard')
    
    elif user.role == 'resident':
        # Get appointment statistics
        all_appointments = Appointment.objects.filter(resident=request.user)
        
        # Count appointments by status
        pending_appointments = all_appointments.filter(status='pending').count()
        approved_appointments = all_appointments.filter(status='approved').count()
        cancelled_appointments = all_appointments.filter(status='cancelled').count()
        completed_appointments = all_appointments.filter(status='completed').count()
        
        # Total appointments
        total_appointments = all_appointments.count()
        
        # Upcoming appointments (next 7 days)
        today = datetime.date.today()
        week_from_now = today + datetime.timedelta(days=7)
        upcoming_appointments = all_appointments.filter(
            preferred_date__gte=today,
            preferred_date__lte=week_from_now
        ).count()
        
        # Next appointment
        next_appointment = all_appointments.filter(
            preferred_date__gte=today,
            status__in=['pending', 'approved']
        ).order_by('preferred_date', 'preferred_time').first()

        context = {
            'user': user,
            'total_appointments': total_appointments,
            'upcoming_appointments': upcoming_appointments,
            'pending_appointments': pending_appointments,
            'approved_appointments': approved_appointments,
            'cancelled_appointments': cancelled_appointments,
            'completed_appointments': completed_appointments,
            'next_appointment': next_appointment,
        }

        return render(request, 'accounts/dashboard.html', context)
    
    else:
        logout(request)
        messages.error(request, 'Invalid account. Please try again.')
        return redirect('login')

@login_required
def staff_dashboard(request):
    user = request.user
    if user.role == 'resident':
        return redirect('dashboard')
    
    pending_count = Appointment.objects.filter(status='pending').count()
    approved_count = Appointment.objects.filter(status='approved').count()
    total_appointments_today = Appointment.objects.filter(preferred_date=datetime.date.today()).count()
    residents_count = get_user_model().objects.filter(role='resident').count()
    
    # Get recent appointments (last 5 created) with prefetched resident data
    recent_appointments = Appointment.objects.select_related('resident__resident').all().order_by('-created_at')[:5]

    context = {
        "pending_count": pending_count,
        "approved_count": approved_count,
        "total_appointments_today": total_appointments_today,
        "residents_count": residents_count,
        "recent_appointments": recent_appointments,
    }

    return render(request, 'accounts/staff_dashboard.html', context)

@login_required
def profile(request):
    user = request.user
    
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, instance=user.resident)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated.')

    else:
        form = CustomUserUpdateForm(instance=user.resident)

    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'accounts/profile.html', context)