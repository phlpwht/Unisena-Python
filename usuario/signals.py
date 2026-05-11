from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Usuario, Rol
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import random

@receiver(post_save, sender=User)
def crear_perfil_usuario_social(sender, instance, created, **kwargs):
    """
    Esta función se ejecuta cada vez que se guarda un Usuario.
    Si el usuario es nuevo (created=True), se le crea automáticamente
    un registro en la tabla de Usuario personalizada con el rol de Cliente.
    """
    if created:
        # Buscamos o creamos el rol de Cliente (ID 2 según tu registro_view)
        rol_cliente, _ = Rol.objects.get_or_create(nombre_rol="Cliente")
        
        nombres_user = instance.first_name or "Usuario"

        # Verificamos si ya existe el usuario en nuestra tabla personalizada por su correo
        if not Usuario.objects.filter(correo=instance.email).exists():
            # Creamos el usuario vinculado con datos por defecto para los campos obligatorios
            Usuario.objects.create(
                rol=rol_cliente,
                nombres=nombres_user,
                apellidos=instance.last_name or "Google",
                correo=instance.email,
                fecha_nacimiento=timezone.now().date(), # Valor por defecto necesario
                tipo_identificacion='CC',               # Valor por defecto necesario
                num_identificacion=str(random.randint(100000, 99999999)), # ID aleatorio único
                password=str(random.random()) # Contraseña dummy (no se usa en login social)
            )

            # --- Lógica de envío de correo (Copiada de tu registro_view) ---
            asunto = "Bienvenido a UniSena 🎉"
            mensaje_texto = f"Hola {nombres_user}, tu cuenta fue creada correctamente."
            mensaje_html = f"""
            <html>
            <body style="font-family: Arial; background-color: #f5f7fa; padding: 20px;">
                <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px; text-align: center;">
                <img src="https://i.imgur.com/2yaf2wb.png" width="80" style="margin-bottom: 10px;" />
                <h2 style="color: #125f58;">Bienvenido a UniSena</h2>
                <p style="color: #555;">
                    Hola <strong>{nombres_user}</strong>, tu cuenta fue creada correctamente vía Google 🎉
                </p>
                <p style="color: #777;">
                    Ya puedes iniciar sesión y empezar a comprar o vender uniformes.
                </p>
                <hr style="margin: 20px 0;">
                <small style="color: #aaa;">
                    © 2026 UniSena
                </small>
                </div>
            </body>
            </html>
            """

            email_bienvenida = EmailMultiAlternatives(
                asunto,
                mensaje_texto,
                settings.DEFAULT_FROM_EMAIL,
                [instance.email]
            )
            email_bienvenida.attach_alternative(mensaje_html, "text/html")
            
            try:
                email_bienvenida.send()
                print(f"📧 Correo de bienvenida enviado a: {instance.email}")
            except Exception as e:
                print(f"🚨 Error enviando correo social: {e}")

            print(f"✅ Usuario de Google creado como Cliente en la base de datos: {instance.email}")

@receiver(user_logged_in)
def vincular_sesion_social(sender, request, user, **kwargs):
    """Sincroniza el login de Google con el sistema de sesiones de tu app."""
    try:
        usuario_p = Usuario.objects.get(correo=user.email)
    except Usuario.DoesNotExist:
        # Fallback de seguridad: si por algún motivo no se creó en el post_save
        rol_cliente, _ = Rol.objects.get_or_create(nombre_rol="Cliente")
        usuario_p = Usuario.objects.create(
            rol=rol_cliente,
            nombres=user.first_name or "Usuario",
            apellidos=user.last_name or "Google",
            correo=user.email,
            fecha_nacimiento=timezone.now().date(),
            tipo_identificacion='CC',
            num_identificacion=str(random.randint(100000, 99999999)),
            password=str(random.random())
        )

    # Configuramos la sesión para que el resto de la app (carrito, locales) te reconozca
    request.session["usuario_id"] = usuario_p.id
    request.session["usuario_nombre"] = usuario_p.nombres
    request.session["usuario_rol"] = usuario_p.rol.nombre_rol
    request.session.modified = True