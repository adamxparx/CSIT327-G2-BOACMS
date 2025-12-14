from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomLoginView

urlpatterns = [

    path('', views.index, name='index'),

    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
    path('register/', views.register, name='register'),
    
    path('staff_dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('profile/', views.profile, name='profile'),
    path('create_staff_account/', views.create_staff_account, name='create_staff_account'),
    path('clear_approval_modal/', views.clear_approval_modal, name='clear_approval_modal'),
    path('approve_resident/<int:resident_id>/', views.approve_resident, name='approve_resident'),
    path('reject_resident/<int:resident_id>/', views.reject_resident, name='reject_resident'),
    path('resident_approvals/', views.resident_approvals, name='resident_approvals'),

]