from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [
    # Public URLs
    path('', views.index, name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),
    path('clear_approval_modal/', views.clear_approval_modal, name='clear_approval_modal'),
    
    # Admin URLs
    path('admin/', admin.site.urls),
    path('administrator/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('administrator/resident-verification/', views.resident_verification, name='resident_verification'),
    path('administrator/resident/<int:resident_id>/', views.resident_detail, name='resident_detail'),
    path('administrator/staff-accounts/', views.staff_accounts, name='staff_accounts'),
    path('administrator/create-staff/', views.create_staff_account, name='create_staff_account'),
    path('administrator/staff/<int:staff_id>/toggle/', views.toggle_staff_status, name='toggle_staff_status'),
    
    
    # Additional Admin URLs for new features
    path('administrator/reports/', views.admin_reports, name='admin_reports'),
    path('administrator/settings/', views.admin_settings, name='admin_settings'),
    path('administrator/activity-log/', views.activity_log, name='activity_log'),
    path('administrator/generate-report/', views.generate_report, name='generate_report'),
    path('administrator/announcements/', views.announcements, name='announcements'),
    path('administrator/profile/', views.admin_profile, name='admin_profile'),
    
    # Staff URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/resident-approvals/', views.resident_approvals, name='resident_approvals'),
    path('staff/approve-resident/<int:resident_id>/', views.approve_resident, name='approve_resident'),
    path('staff/reject-resident/<int:resident_id>/', views.reject_resident, name='reject_resident'),
    path('staff/update-appointment-status/', views.update_appointment_status, name='update_appointment_status'),
    
    # Resident URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Debug URL
    path('debug-role/', views.debug_role, name='debug_role'),
]