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

]