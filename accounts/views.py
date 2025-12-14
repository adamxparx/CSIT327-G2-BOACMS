from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm, CustomUserUpdateForm, ResidentForm, StaffCreationForm
from appointments.models import Appointment
from django.contrib.auth import get_user_model
import datetime
from .utils import upload_document_to_supabase
from .models import Resident


def auth_check(user, is_new_registration=False):
    if user.is_authenticated and not is_new_registration:
        if user.role == 'resident':
            # Check if the resident account is approved
            try:
                if hasattr(user, 'resident') and user.resident.approval_status != 'approved':
                    # If not approved, redirect to login with a message
                    return redirect('login')
                else:
                    return redirect('dashboard')
            except:
                # If there's an issue accessing the resident record, redirect to login
                return redirect('login')
        elif user.role == 'staff':
            return redirect('staff_dashboard')
    return None


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if this is a new registration
        is_new_registration = 'new_registration' in request.GET
        response = auth_check(request.user, is_new_registration)
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
        resident_form = ResidentForm(request.POST, request.FILES)
        if user_form.is_valid() and resident_form.is_valid():
            user = user_form.save()
            resident = resident_form.save(commit=False)
            resident.user = user
            
            # Handle document upload to Supabase if provided
            address_document = request.FILES.get('address_document_file')
            if address_document:
                try:
                    # Upload to Supabase and get the URL
                    document_url = upload_document_to_supabase(address_document, user.id)
                    resident.address_document = document_url
                except Exception as e:
                    messages.error(request, f'Failed to upload document: {str(e)}')
                    # Delete the user if document upload fails
                    user.delete()
                    return render(request, 'accounts/register.html', {
                        'user_form': user_form,
                        'resident_form': resident_form,
                    })
            
            resident.approval_status = 'pending'
            resident.save()
            # Redirect to login with a flag indicating new registration
            return redirect('{}?new_registration=true'.format(reverse('login')))
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
        # Check if the resident account is approved
        if hasattr(user, 'resident') and user.resident.approval_status != 'approved':
            # If not approved, log out the user and redirect to login with a message
            logout(request)
            messages.error(request, 'Your account is pending approval. Please wait for staff to approve your account.')
            return redirect('login')
        
        # Get appointment statistics
        all_appointments = Appointment.objects.filter(resident=request.user)
        
        # Count appointments by status
        pending_appointments = all_appointments.filter(status='pending').count()
        approved_appointments = all_appointments.filter(status='approved').count()
        cancelled_appointments = all_appointments.filter(status='cancelled').count()
        completed_appointments = all_appointments.filter(status='completed').count()
        claimed_appointments = all_appointments.filter(status='claimed').count()
        
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
            'claimed_appointments': claimed_appointments,
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
def resident_approvals(request):
    """
    View to display all pending resident approvals
    """
    # Check if the user is staff
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_dashboard')
    
    # Get pending resident approvals
    pending_residents = Resident.objects.filter(approval_status='pending').select_related('user').order_by('user__date_joined')
    
    context = {
        "pending_residents": pending_residents,
    }

    return render(request, 'accounts/resident_approvals.html', context)


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


@login_required
def create_staff_account(request):
    """
    View for staff to create new staff accounts
    """
    # Check if the user is staff
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_dashboard')
    
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            first_name = form.cleaned_data.get('first_name')
            middle_name = form.cleaned_data.get('middle_name')
            last_name = form.cleaned_data.get('last_name')
            
            # Build full name for the message
            if middle_name:
                full_name = f'{first_name} {middle_name} {last_name}'
            else:
                full_name = f'{first_name} {last_name}'
                
            messages.success(request, f'Staff account for {full_name} ({user.email}) has been created successfully!')
            return redirect('staff_dashboard')
    else:
        form = StaffCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/create_staff_account.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def clear_approval_modal(request):
    """
    View to clear the approval modal flag from the session
    """
    if 'show_approval_modal' in request.session:
        del request.session['show_approval_modal']
    return HttpResponse(status=204)


@login_required
def approve_resident(request, resident_id):
    """
    View to approve a resident account
    """
    # Check if the user is staff
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_dashboard')
    
    try:
        resident = Resident.objects.get(id=resident_id)
        resident.approval_status = 'approved'
        resident.approval_date = datetime.datetime.now()
        resident.save()
        
        # Send approval email
        email_sent = False
        try:
            subject = 'Account Approved - Barangay Office Management System'
            from_email = 'no-reply@barangay-office.com'  # Change this to your actual email
            recipient_list = [resident.user.email]
            
            # Render email templates
            text_content = render_to_string('emails/resident_approval.txt', {'resident': resident})
            html_content = render_to_string('emails/resident_approval.html', {'resident': resident})
            
            # Create and send email
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            email_sent = True
        except Exception as e:
            # If email fails, we still approve the account but log the error
            pass  # In production, you might want to log this error
        
        if email_sent:
            messages.success(request, f'Resident account for {resident.first_name} {resident.last_name} has been approved and notification email sent.')
        else:
            messages.success(request, f'Resident account for {resident.first_name} {resident.last_name} has been approved. (Notification email could not be sent)')
    except Resident.DoesNotExist:
        messages.error(request, 'Resident not found.')
    
    return redirect('staff_dashboard')


@require_http_methods(["POST"])
@csrf_exempt
def clear_approval_modal(request):
    """
    View to clear the approval modal session flag
    """
    if 'show_approval_modal' in request.session:
        del request.session['show_approval_modal']
    return HttpResponse(status=204)


@login_required
def reject_resident(request, resident_id):
    """
    View to reject a resident account
    """
    # Check if the user is staff
    if request.user.role != 'staff':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('staff_dashboard')
    
    try:
        resident = Resident.objects.get(id=resident_id)
        user_email = resident.user.email  # Save email before deleting
        resident_name = f'{resident.first_name} {resident.last_name}'  # Save name before deleting
        
        # Delete the user account
        user = resident.user
        resident.delete()
        user.delete()
        
        # Send rejection email
        email_sent = False
        try:
            subject = 'Account Rejected - Barangay Office Management System'
            from_email = 'no-reply@barangay-office.com'  # Change this to your actual email
            recipient_list = [user_email]
            
            # Render email templates
            text_content = render_to_string('emails/resident_rejection.txt', {'resident': {'first_name': resident_name.split()[0], 'last_name': resident_name.split()[-1]}})
            html_content = render_to_string('emails/resident_rejection.html', {'resident': {'first_name': resident_name.split()[0], 'last_name': resident_name.split()[-1]}})
            
            # Create and send email
            msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            email_sent = True
        except Exception as e:
            # If email fails, we still reject the account but log the error
            pass  # In production, you might want to log this error
        
        if email_sent:
            messages.success(request, f'Resident account for {resident_name} has been rejected and removed. Notification email sent.')
        else:
            messages.success(request, f'Resident account for {resident_name} has been rejected and removed. (Notification email could not be sent)')
    except Resident.DoesNotExist:
        messages.error(request, 'Resident not found.')
    
    return redirect('staff_dashboard')