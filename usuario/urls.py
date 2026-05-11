from django.urls import path
from . import views

urlpatterns = [

    # 🌍 LANDING (lo primero que se ve)
    path('', views.landing, name='landing'),

    # 🔐 LOGIN
    path('login/', views.login_view, name='login'),

    # 📋 REGISTRO
    path('registro/', views.registro_view, name='registro'),

    # 🔒 PROTEGIDAS
    path('inicio-cliente/', views.inicio_cliente, name='inicio_cliente'),
    path('inicio-admin/', views.inicio_admin, name='inicio_admin'),
    path('inicio-vendedor/', views.inicio_vendedor, name='inicio_vendedor'),

    path('logout/', views.logout_view, name='logout'),
    
    # 🛠️ OTRAS RUTAS (ej: restablecer contraseña)
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
]