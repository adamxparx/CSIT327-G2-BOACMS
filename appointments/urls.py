from django.urls import path
from . import views
from .views import RequirementsView

urlpatterns = [
    path('appointments/', views.appointments, name='appointments'),
    path('staff_appointments/', views.staff_appointments, name='staff_appointments'),
    path('approved_appointments/', views.approved_appointments, name='approved_appointments'),
    path('pending_appointments/', views.pending_appointments, name='pending_appointments'),
    path('cancelled_appointments/', views.cancelled_appointments, name='cancelled_appointments'),
    path('completed_appointments/', views.completed_appointments, name='completed_appointments'),
    path('certification/', views.create_appointment, name='certification'),
    path('confirmation/<int:appointment_id>/', views.confirmation, name='confirmation'),
    path('cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('requirements/', RequirementsView.as_view(), name='requirements'),
    path('api/appointments/', views.api_appointments_list, name='api_appointments_list'),
    path('calendar/', views.appointments_calendar_view, name='appointments_calendar'),
    path('appointment/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
]