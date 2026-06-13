from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashadmin, name='admin_dashboard'),
]