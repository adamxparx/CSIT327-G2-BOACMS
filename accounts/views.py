from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
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
from django.contrib.auth.decorators import user_passes_test
from .models import CustomUser, Resident, BarangayStaff
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_staff(user):
    return user.is_authenticated and user.role == 'staff'

def is_resident(user):
    return user.is_authenticated and user.role == 'resident'

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
        elif user.role == 'admin':
            return redirect('admin_dashboard')
    return None


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def get_success_url(self):
        user = self.request.user
        
        if user.role == 'resident':
            # Check if resident is approved
            try:
                if hasattr(user, 'resident') and user.resident.approval_status != 'approved':
                    messages.error(self.request, 'Your account is pending approval. Please wait for approval.')
                    return reverse('login')
            except:
                pass
            return reverse('dashboard')
        elif user.role == 'staff':
            return reverse('staff_dashboard')
        elif user.role == 'admin':
            return reverse('admin_dashboard')
        else:
            return reverse('index')
    
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
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        resident_form = ResidentForm(request.POST, request.FILES)
        
        if user_form.is_valid() and resident_form.is_valid():
            # Create user account
            user = user_form.save(commit=False)
            user.role = 'resident'
            user.is_active = True  # Allow login but pending approval
            user.save()
            
            # Create resident profile
            resident = resident_form.save(commit=False)
            resident.user = user
            resident.approval_status = 'pending'
            resident.barangay = 'Labangon'
            resident.city = 'Cebu City'
            resident.save()

            
            
            # Redirect to register page with success parameter
            return redirect(reverse('register') + '?success=true')
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
    
    elif user.role == 'admin':
        return redirect('admin_dashboard')
    
    elif user.role == 'resident':
        # Check if the resident account is approved
        if hasattr(user, 'resident') and user.resident.approval_status != 'approved':
            # If not approved, log out the user and redirect to login with a message
            logout(request)
            messages.error(request, 'Your account is pending approval. Please wait for approval.')
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
    if request.user.role not in ['staff', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
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
    if request.user.role not in ['staff', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
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
    if request.user.role not in ['staff', 'admin']:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('dashboard')
    
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


# ===============================
# ADMIN VIEWS
# ===============================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard - enhanced version"""
    today = timezone.now().date()
    
    # Core statistics
    pending_verifications = Resident.objects.filter(approval_status='pending').count()
    approved_residents = Resident.objects.filter(approval_status='approved').count()
    active_staff = CustomUser.objects.filter(role='staff', is_active=True).count()
    
    # Total users (all roles)
    total_users = CustomUser.objects.all().count()
    
    # Recent registrations (last 5)
    recent_registrations = Resident.objects.select_related('user').order_by('-user__date_joined')[:5]
    
    # Recent approvals (last 5)
    recent_approvals = Resident.objects.filter(
        approval_status='approved',
        approval_date__isnull=False
    ).select_related('user').order_by('-approval_date')[:5]
    
    context = {
        'pending_verifications': pending_verifications,
        'approved_residents': approved_residents,
        'active_staff': active_staff,
        'total_users': total_users,
        'recent_registrations': recent_registrations,
        'recent_approvals': recent_approvals,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def resident_verification(request):
    """Admin view to see all resident verifications in table format"""
    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    residents = Resident.objects.select_related('user').all()
    
    # Apply status filter
    if status_filter == 'pending':
        residents = residents.filter(approval_status='pending')
    elif status_filter == 'approved':
        residents = residents.filter(approval_status='approved')
    elif status_filter == 'rejected':
        # Note: Rejected residents are deleted, so we can't filter by status
        residents = Resident.objects.none()  # Empty queryset
    
    # Apply search filter
    if search_query:
        residents = residents.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Order by date joined (newest first)
    residents = residents.order_by('-user__date_joined')
    
    # Get counts for each status
    pending_count = Resident.objects.filter(approval_status='pending').count()
    approved_count = Resident.objects.filter(approval_status='approved').count()
    total_count = Resident.objects.all().count()
    
    context = {
        'pending_residents': residents,
        'status_filter': status_filter,
        'search_query': search_query,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'total_count': total_count,
    }
    return render(request, 'accounts/resident_verification.html', context)


@login_required
@user_passes_test(is_admin)
def resident_detail(request, resident_id):
    """Admin view to see resident details and approve/reject"""
    try:
        resident = Resident.objects.get(id=resident_id)
    except Resident.DoesNotExist:
        messages.error(request, 'Resident not found.')
        return redirect('resident_verification')
    
    # Get related appointments
    appointments = Appointment.objects.filter(resident=resident.user).order_by('-created_at')[:5]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()
        
        if action == 'approve':
            # Approve the resident
            resident.approval_status = 'approved'
            resident.approval_date = timezone.now()
            resident.approval_notes = notes if notes else 'Approved by admin'
            resident.save()
            
            # Send approval email
            try:
                subject = 'Account Approved - Barangay Office Management System'
                from_email = 'no-reply@barangay-office.com'
                recipient_list = [resident.user.email]
                
                text_content = render_to_string('emails/resident_approval.txt', {'resident': resident})
                html_content = render_to_string('emails/resident_approval.html', {'resident': resident})
                
                msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                messages.success(request, f'Resident {resident.first_name} {resident.last_name} approved. Email sent.')
            except Exception as e:
                messages.success(request, f'Resident {resident.first_name} {resident.last_name} approved. (Email failed to send)')
            
            return redirect('resident_verification')
            
        elif action == 'reject':
            # Reject the resident
            user_email = resident.user.email
            resident_name = f'{resident.first_name} {resident.last_name}'
            user = resident.user
            
            # Store notes before deletion
            rejection_reason = notes if notes else 'Account did not meet requirements'
            
            # Send rejection email
            try:
                subject = 'Account Rejected - Barangay Office Management System'
                from_email = 'no-reply@barangay-office.com'
                recipient_list = [user_email]
                
                context = {
                    'resident': {
                        'first_name': resident.first_name,
                        'last_name': resident.last_name,
                        'rejection_reason': rejection_reason
                    }
                }
                
                text_content = render_to_string('emails/resident_rejection.txt', context)
                html_content = render_to_string('emails/resident_rejection.html', context)
                
                msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            except Exception as e:
                pass
            
            # Delete the accounts
            resident.delete()
            user.delete()
            
            messages.success(request, f'Resident {resident_name} rejected and removed.')
            return redirect('resident_verification')
    
    context = {
        'resident': resident,
        'appointments': appointments,
        'document_types': {
            'address_document': 'Proof of Address',
            'id_document': 'Government ID',
            'birth_certificate': 'Birth Certificate',
        }
    }
    return render(request, 'accounts/resident_detail.html', context)


@login_required
@user_passes_test(is_admin)
def staff_accounts(request):
    """Admin view to manage staff accounts"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    staff_members = CustomUser.objects.filter(role='staff').select_related('barangaystaff')

    active_count = staff_members.filter(is_active=True).count()
    inactive_count = staff_members.filter(is_active=False).count()
    
    # Apply search filter
    if search_query:
        staff_members = staff_members.filter(
            Q(email__icontains=search_query) |
            Q(barangaystaff__first_name__icontains=search_query) |
            Q(barangaystaff__last_name__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'active':
        staff_members = staff_members.filter(is_active=True)
    elif status_filter == 'inactive':
        staff_members = staff_members.filter(is_active=False)
    
    # Get counts
    active_count = CustomUser.objects.filter(role='staff', is_active=True).count()
    inactive_count = CustomUser.objects.filter(role='staff', is_active=False).count()
    total_count = active_count + inactive_count
    
    context = {
        'staff_members': staff_members,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_count': total_count,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'accounts/staff_accounts.html', context)


@login_required
@user_passes_test(is_admin)
def create_staff_account(request):
    """View for admin to create new staff accounts"""
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'staff'  # Ensure role is set to staff
            user.save()
            
            # Create associated BarangayStaff record
            BarangayStaff.objects.create(
                user=user,
                first_name=form.cleaned_data.get('first_name'),
                middle_name=form.cleaned_data.get('middle_name'),
                last_name=form.cleaned_data.get('last_name')
            )
            
            messages.success(request, f'Staff account created successfully!')
            return redirect('staff_accounts')
    else:
        form = StaffCreationForm()
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/create_staff_account.html', context)


@login_required
@user_passes_test(is_admin)
def toggle_staff_status(request, staff_id):
    """Activate or deactivate staff account"""
    try:
        staff_user = CustomUser.objects.get(id=staff_id, role='staff')
        if staff_user.is_active:
            staff_user.is_active = False
            action = 'deactivated'
        else:
            staff_user.is_active = True
            action = 'activated'
        staff_user.save()
        messages.success(request, f'Staff account {action} successfully.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'Staff account not found.')
    
    return redirect('staff_accounts')


# ===============================
# ADMIN ADDITIONAL VIEWS
# ===============================

@login_required
@user_passes_test(is_admin)
def admin_reports(request):
    """Admin reports page"""
    # Get report statistics
    today = timezone.now().date()
    month_start = today.replace(day=1)
    
    # Monthly statistics
    monthly_registrations = Resident.objects.filter(
        created_at__date__gte=month_start
    ).count()
    
    monthly_appointments = Appointment.objects.filter(
        preferred_date__gte=month_start
    ).count()
    
    # Status breakdowns
    appointment_statuses = Appointment.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    resident_statuses = Resident.objects.values('approval_status').annotate(
        count=Count('id')
    )
    
    # Staff activity
    active_staff_count = CustomUser.objects.filter(role='staff', is_active=True).count()
    
    context = {
        'monthly_registrations': monthly_registrations,
        'monthly_appointments': monthly_appointments,
        'appointment_statuses': appointment_statuses,
        'resident_statuses': resident_statuses,
        'active_staff_count': active_staff_count,
        'report_date': today,
    }
    return render(request, 'accounts/admin_reports.html', context)


@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """Admin settings page"""
    return render(request, 'accounts/admin_settings.html')


@login_required
@user_passes_test(is_admin)
def activity_log(request):
    """Activity log page"""
    # Get recent activities from various models
    today = timezone.now().date()
    
    # Recent resident registrations
    recent_registrations = Resident.objects.select_related('user').order_by('-created_at')[:10]
    
    # Recent appointments
    recent_appointments = Appointment.objects.select_related('resident__user').order_by('-created_at')[:10]
    
    # Recent staff actions
    recent_staff_actions = CustomUser.objects.filter(
        role='staff'
    ).order_by('-date_joined')[:5]
    
    context = {
        'recent_registrations': recent_registrations,
        'recent_appointments': recent_appointments,
        'recent_staff_actions': recent_staff_actions,
        'today': today,
    }
    return render(request, 'accounts/activity_log.html', context)


@login_required
@user_passes_test(is_admin)
def generate_report(request):
    """Generate report view"""
    report_type = request.GET.get('type', 'daily')
    
    if report_type == 'daily':
        # Generate daily report
        today = timezone.now().date()
        new_registrations = Resident.objects.filter(
            created_at__date=today
        ).count()
        
        appointments_today = Appointment.objects.filter(
            preferred_date=today
        ).count()
        
        # You would typically generate a PDF or Excel file here
        messages.success(request, f'Daily report generated: {new_registrations} new registrations, {appointments_today} appointments today.')
        
    elif report_type == 'monthly':
        # Generate monthly report
        today = timezone.now().date()
        month_start = today.replace(day=1)
        
        monthly_registrations = Resident.objects.filter(
            created_at__date__gte=month_start
        ).count()
        
        monthly_appointments = Appointment.objects.filter(
            preferred_date__gte=month_start
        ).count()
        
        messages.success(request, f'Monthly report generated: {monthly_registrations} registrations, {monthly_appointments} appointments this month.')
    
    return redirect('admin_reports')


@login_required
@user_passes_test(is_admin)
def announcements(request):
    """Announcements management"""
    if request.method == 'POST':
        # Handle announcement creation
        title = request.POST.get('title')
        message = request.POST.get('message')
        recipient_type = request.POST.get('recipient_type', 'all')
        
        if title and message:
            # Here you would save the announcement and schedule sending
            messages.success(request, 'Announcement scheduled for sending.')
        else:
            messages.error(request, 'Please provide both title and message.')
    
    return render(request, 'accounts/announcements.html')


@login_required
@user_passes_test(is_admin)
def admin_profile(request):
    """Admin profile page"""
    user = request.user
    
    if request.method == 'POST':
        # Handle profile update
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        if first_name and last_name and email:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'user': user,
    }
    return render(request, 'accounts/admin_profile.html', context)


def debug_role(request):
    if request.user.is_authenticated:
        return HttpResponse(f"""
        <h1>DEBUG: User Role</h1>
        <p>Email: {request.user.email}</p>
        <p>Role: {request.user.role}</p>
        <p>Is Admin: {request.user.role == 'admin'}</p>
        <p>Is Staff: {request.user.role == 'staff'}</p>
        <p>Full Name: {request.user.get_full_name()}</p>
        <hr>
        <a href="/administrator/dashboard/">Try Admin Dashboard</a><br>
        <a href="/staff/dashboard/">Try Staff Dashboard</a><br>
        <a href="/dashboard/">Try Resident Dashboard</a>
        """)
    return HttpResponse("Not logged in")