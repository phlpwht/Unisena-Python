from django.shortcuts import render,redirect
from django.core.paginator import Paginator
from django.contrib import messages
from uniformes.models import Prendas
from .models import Usuario,Rol
from uniformes.models import Pedido, EstadoPedido
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import logout
import random, datetime, re
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import OuterRef, Subquery
from django.views.decorators.cache import never_cache



def login_view(request):

    # Si el usuario llega desde un botón de "Añadir al carrito" sin estar logueado
    # le mostramos el mensaje de advertencia de forma proactiva.
    if not request.session.get("usuario_id") and request.GET.get("auth") == "1":
        messages.warning(request, "Debes iniciar sesión para agregar productos al carrito 🔒")

    if request.method == "POST":

        correo = request.POST.get("correo")
        password = request.POST.get("password")

        try:
            usuario = Usuario.objects.get(correo=correo)

            if check_password(password, usuario.password):

                print("ROL DEL USUARIO:", usuario.rol_id)

                request.session["usuario_id"] = usuario.id
                request.session["usuario_nombre"] = f"{usuario.nombres} {usuario.apellidos}"
                request.session["usuario_rol"] = usuario.rol.nombre_rol


                if usuario.rol.nombre_rol == "Administrador":
                    return redirect("inicio_admin")

                elif usuario.rol.nombre_rol == "Cliente" or usuario.rol.nombre_rol == "Vendedor":
                    # Ambos roles van al inicio del cliente para ver el catálogo
                    return redirect("inicio_cliente")
                
                else:
                    return render(request, "login.html", {"error": "Rol no válido"})

            else:
                return render(request, "login.html", {"error": "Correo o contraseña incorrectos"})

        except Usuario.DoesNotExist:
            return render(request, "login.html", {"error": "Usuario no existe"})

    return render(request, "login.html")

@never_cache
def inicio_admin(request):

    if "usuario_id" not in request.session:
        return redirect("login")

    if request.session.get("usuario_rol") != "Administrador":
        return redirect("login")

    nombre = request.session.get("usuario_nombre")

    return render(request, "admin.html", {"nombre": nombre})

@never_cache
def landing(request):

    # Si el usuario ya está logueado y es Admin, mandarlo a su panel de una
    if request.session.get("usuario_rol") == "Administrador":
        return redirect("inicio_admin")

    nombre = request.session.get("usuario_nombre")
    rol = request.session.get("usuario_rol")
    usuario_id = request.session.get("usuario_id")
    
    # Calculamos el carrito para Clientes o usuarios no logueados (Anónimos)
    cart_count = 0
    if rol != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    # Contar pedidos donde el estado MÁS RECIENTE sea 'PENDIENTE'
    pedidos_pendientes_count = 0
    if usuario_id:
        pedidos_pendientes_count = Pedido.objects.filter(
            usuario_id=usuario_id,
            estado__estado_pedido='PENDIENTE'
        ).count()

    # Obtenemos uniformes de locales que estén activos
    prendas_qs = Prendas.objects.filter(idLocal__EstaActivo=True, activo=True).select_related('idLocal', 'idLocal__IdUsuario')
    
    return render(request, "inicio_cliente.html", {
        "nombre": nombre,
        "rol": rol,
        "prendas": prendas_qs,
        "cart_count": cart_count,
        "pedidos_pendientes_count": pedidos_pendientes_count,
    })
    

@never_cache
def inicio_cliente(request):

    if "usuario_id" not in request.session:
        return redirect("login")

    rol = request.session.get("usuario_rol")
    
    # Si un Admin intenta entrar aquí (inicio de cliente), lo mandamos a su panel
    if rol == "Administrador":
        return redirect("inicio_admin")

    if str(rol) not in ["Cliente", "Vendedor"]:
        return redirect("login")

    nombre = request.session.get("usuario_nombre")
    rol = request.session.get("usuario_rol")
    usuario_id = request.session.get("usuario_id")

    # Calculamos el carrito para Clientes o usuarios no logueados
    cart_count = 0
    if rol != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    # 🛒 Obtenemos uniformes de locales que estén activos para que siempre aparezcan
    prendas_qs = Prendas.objects.filter(idLocal__EstaActivo=True, activo=True).select_related('idLocal', 'idLocal__IdUsuario')
    
    # Contar cuántos pedidos pendientes tiene el cliente
    pedidos_pendientes_count = Pedido.objects.filter(
        usuario_id=usuario_id,
        estado__estado_pedido='PENDIENTE'
    ).count()

    return render(request, "inicio_cliente.html", {
        "nombre": nombre,
        "rol": rol,
        "prendas": prendas_qs,
        "cart_count": cart_count,
        "pedidos_pendientes_count": pedidos_pendientes_count,
    })

def inicio_vendedor(request):

    if "usuario_id" not in request.session:
        return redirect("login")

    if request.session.get("usuario_rol") != "Vendedor":
        return redirect("login")

    return redirect("inicio_cliente")

def logout_view(request):
    logout(request)
    return redirect("landing")

def registro_view(request):

    if request.method == "POST":

        nombres = request.POST["nombres"]
        apellidos = request.POST["apellidos"]
        email_destino = request.POST["correo"]
        fecha_nacimiento = request.POST["fecha_nacimiento"]
        tipo_identificacion = request.POST["tipo_identificacion"]
        num_identificacion = request.POST["num_identificacion"]
        password = request.POST["password"]

        # --- VALIDACIÓN DE CARACTERES Y LONGITUD (MODELO: 50) ---
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', nombres) or len(nombres) > 50:
            messages.error(request, "❌ Nombres no válidos (Solo letras, máx 50 caracteres).")
            return render(request, "registro.html")

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', apellidos) or len(apellidos) > 50:
            messages.error(request, "❌ Apellidos no válidos (Solo letras, máx 50 caracteres).")
            return render(request, "registro.html")

        # --- VALIDACIÓN DE LONGITUD DE CONTRASEÑA ---
        if len(password) < 8 or len(password) > 20:
            messages.error(request, "❌ La contraseña debe tener entre 8 y 20 caracteres.")
            return render(request, "registro.html")

        # --- VALIDACIÓN DE FECHA DE NACIMIENTO ---
        try:
            # Convertimos la cadena de la fecha en un objeto de fecha
            fecha_nac_dt = datetime.datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            hoy = now().date()
            
            # 1. Que no sea mayor que el año actual (Fecha futura)
            if fecha_nac_dt > hoy:
                messages.error(request, "❌ La fecha de nacimiento no puede ser mayor que la fecha actual.")
                return render(request, "registro.html")
            
            # 2. Que no sea "menor" de 60 años (Interpretado como: Máximo 60 años de edad)
            # Calculamos la edad exacta
            edad = hoy.year - fecha_nac_dt.year - ((hoy.month, hoy.day) < (fecha_nac_dt.month, fecha_nac_dt.day))
            
            if edad > 70:
                messages.error(request, "⚠️ ¡Atención! El límite de edad para el registro en UniSena es de 70 años. ¡Agradecemos mucho tu interés! ✨")
                return render(request, "registro.html")
                
        except (ValueError, TypeError):
            messages.error(request, "❌ Formato de fecha de nacimiento no válido.")
            return render(request, "registro.html")
        # --- FIN VALIDACIÓN ---

        if Usuario.objects.filter(num_identificacion=num_identificacion).exists():
            messages.error(request, "El número de identificación ya está registrado.")
            return render(request, "registro.html")


        if not num_identificacion.isdigit() or len(num_identificacion) > 15:
            messages.error(request, "❌ Identificación no válida (Solo números, máx 15 dígitos).")
            return render(request, "registro.html")

        if Usuario.objects.filter(correo=email_destino).exists():
            messages.error(request, "El correo ya se encuentra registrado.")
            return render(request, "registro.html")


        rol = Rol.objects.get(id=2)

        usuario = Usuario(
            rol=rol,
            nombres=nombres,
            apellidos=apellidos,
            correo=email_destino,
            fecha_nacimiento=fecha_nacimiento,
            tipo_identificacion=tipo_identificacion,
            num_identificacion=num_identificacion,
            password=make_password(password)
        )

        usuario.save()

        asunto = "Bienvenido a UniSena 🎉"

        mensaje_texto = f"Hola {nombres}, tu cuenta fue creada correctamente."

        mensaje_html = f"""
        <html>
        <body style="font-family: Arial; background-color: #f5f7fa; padding: 20px;">

            <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px; padding: 20px; text-align: center;">

            <!-- LOGO -->
            <img src="https://i.imgur.com/2yaf2wb.png" width="80" style="margin-bottom: 10px;" />

            <h2 style="color: #125f58;">Bienvenido a UniSena</h2>

            <p style="color: #555;">
                Hola <strong>{nombres}</strong>, tu cuenta fue creada correctamente 🎉
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
            [email_destino]
        )

        email_bienvenida.attach_alternative(mensaje_html, "text/html")
        try:
            email_bienvenida.send()
        except Exception as e:
            print(f"🚨 Error al enviar correo de bienvenida: {e}")

        messages.success(request, "Usuario registrado correctamente.")

        return redirect("login") # Aseguramos que redirija al login

    return render(request, "registro.html")

def recuperar_password(request):

    if request.method == "POST":
        correo = request.POST.get("correo")

        try:
            usuario = Usuario.objects.get(correo=correo)

            # 🔢 generar código de 6 dígitos
            codigo = str(random.randint(100000, 999999))

            usuario.reset_codigo = codigo
            usuario.reset_codigo_fecha = now()
            usuario.save()

            # 📩 correo bonito
            mensaje_html = f"""
            <div style="font-family: Arial; text-align:center;">
                <h2 style="color:#125f58;">Recuperar contraseña</h2>
                <p>Tu código es:</p>
                <h1 style="letter-spacing:5px;">{codigo}</h1>
                <p>No lo compartas con nadie</p>
            </div>
            """

            email = EmailMultiAlternatives(
                "Código de recuperación",
                "Tu código es " + codigo,
                settings.DEFAULT_FROM_EMAIL,
                [correo]
            )

            email.attach_alternative(mensaje_html, "text/html")
            try:
                email.send()
            except Exception as e:
                print(f"🚨 Error al enviar código de recuperación: {e}")

              # 🔴 AÑADIDO

            request.session["correo_reset"] = correo  # 🔴 AÑADIDO para mantener el correo en la sesión

            # 🔥 redirige a donde se pone el código
            return redirect("reset_password")

        except Usuario.DoesNotExist:
            return render(request, "recuperar.html", {"error": "Correo no registrado"})

    return render(request, "recuperar.html")

def reset_password(request):

    correo = request.session.get("correo_reset")

    if not correo:
        return redirect("recuperar")

    try:
        usuario = Usuario.objects.get(correo=correo)
    except Usuario.DoesNotExist:
        return redirect("recuperar")

    if request.method == "POST":

        accion = request.POST.get("accion")

        # 🔁 REENVIAR CÓDIGO
        if accion == "reenviar":
            import random

            codigo = str(random.randint(100000, 999999))

            usuario.reset_codigo = codigo
            usuario.reset_codigo_fecha = now()
            usuario.reset_intentos = 0
            usuario.save()


            mensaje_html = f"""
            <div style="text-align:center;">
                <h2>Nuevo código</h2>
                <h1>{codigo}</h1>
            </div>
            """

            email = EmailMultiAlternatives(
                "Nuevo código",
                "Tu código es " + codigo,
                settings.DEFAULT_FROM_EMAIL,
                [correo]
            )

            email.attach_alternative(mensaje_html, "text/html")
            try:
                email.send()
            except Exception as e:
                print(f"🚨 Error al reenviar código: {e}")

            return render(request, "reset.html", {
                "success": "Se envió un nuevo código"
            })

        # 🔐 CAMBIAR CONTRASEÑA
        elif accion == "cambiar":

            codigo = request.POST.get("codigo")
            password = request.POST.get("password")


            if not usuario.reset_codigo_fecha:
                return render(request, "reset.html", {"error": "Solicita un código primero"})

            if now() > usuario.reset_codigo_fecha + timedelta(minutes=5):
                return render(request, "reset.html", {"error": "Código expirado"})

            if usuario.reset_intentos >= 3:
                return render(request, "reset.html", {"error": "Demasiados intentos"})

            if usuario.reset_codigo != codigo:
                usuario.reset_intentos += 1
                usuario.save()

                return render(request, "reset.html", {
                    "error": f"Código incorrecto ({usuario.reset_intentos}/3)"
                })

            # ✅ contraseña correcta
            usuario.password = make_password(password)
            usuario.reset_codigo = None
            usuario.reset_codigo_fecha = None
            usuario.reset_intentos = 0
            usuario.save()

            del request.session["correo_reset"]

            return redirect("login")

    return render(request, "reset.html")
