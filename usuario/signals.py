from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario, Rol
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
import random

@receiver(user_logged_in)
def vincular_sesion_social(sender, request, user, **kwargs):
    """Sincroniza el login de Google con el sistema de sesiones de tu app."""
    
    social_acc = SocialAccount.objects.filter(user=user).first()

    nombres_google = "Usuario"
    apellidos_google = "Google"

    if social_acc:
        extra_data = social_acc.extra_data

        nombres_google = (
            extra_data.get('given_name')
            or extra_data.get('name')
            or "Usuario"
        )

        apellidos_google = (
            extra_data.get('family_name')
            or "Google"
        )
        
        # Actualizamos también el User de Django para que los mensajes de Allauth salgan bien
        user.first_name = nombres_google
        user.last_name = apellidos_google
        user.save()

    try:
        usuario_p = Usuario.objects.get(correo=user.email)

        usuario_p.nombres = nombres_google
        usuario_p.apellidos = apellidos_google
        usuario_p.save()

    except Usuario.DoesNotExist:
        rol_cliente, _ = Rol.objects.get_or_create(
            nombre_rol="Cliente"
        )

        while True:
            new_num_identificacion = str(
                random.randint(100000000, 999999999)
            )

            if not Usuario.objects.filter(
                num_identificacion=new_num_identificacion
            ).exists():
                break

        usuario_p = Usuario.objects.create(
            rol=rol_cliente,
            nombres=nombres_google,
            apellidos=apellidos_google,
            correo=user.email,
            fecha_nacimiento=timezone.now().date(),
            tipo_identificacion='CC',
            num_identificacion=new_num_identificacion,
            password=str(random.random())
        )

    request.session["usuario_id"] = usuario_p.id
    request.session["usuario_nombre"] = f"{usuario_p.nombres} {usuario_p.apellidos}"
    request.session["usuario_rol"] = usuario_p.rol.nombre_rol
    request.session.modified = True

    
    