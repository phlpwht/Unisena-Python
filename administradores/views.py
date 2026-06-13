from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from usuario.models import Usuario, Rol
from uniformes.models import Pedido, EstadoPedido, Prendas
from locales.models import Local
from django.db.models import Q
from django.db import transaction # Importar transaction
from django.contrib import messages
from django.urls import reverse
from django.middleware.csrf import get_token

@never_cache
def dashadmin(request):
    # Verificación de seguridad: Sesión y Rol de Administrador
    if "usuario_id" not in request.session:
        return redirect("login")

    # Verificamos que sea Administrador
    if request.session.get("usuario_rol") != "Administrador":
        return redirect("login")

    # Detectar qué sección mostrar (por defecto 'inicio')
    section = request.GET.get('section', 'inicio')

    # Procesar acciones POST (Eliminar o Cambiar Rol)
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        accion = request.POST.get("accion")

        if accion == "eliminar":
            with transaction.atomic(): # Usamos una transacción para asegurar la consistencia
                usuario_eliminar = get_object_or_404(Usuario, id=user_id)
                
                # Evitar que el admin se elimine a sí mismo por error
                if str(usuario_eliminar.id) == str(request.session.get("usuario_id")):
                    messages.error(request, "❌ No puedes eliminar tu propia cuenta administrativa.")
                    return redirect(f"{reverse('admin_dashboard')}?section=usuarios")
                
                # Validar si el usuario tiene pedidos pendientes o en proceso (Cliente)
                if usuario_eliminar.rol.nombre_rol == "Cliente":
                    tiene_pedidos_cliente = Pedido.objects.filter(
                        usuario=usuario_eliminar,
                        estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
                    ).exists()
                    if tiene_pedidos_cliente:
                        messages.error(request, f"❌ No se puede eliminar a {usuario_eliminar.nombres} porque tiene pedidos pendientes o en proceso como cliente.")
                        return redirect(f"{reverse('admin_dashboard')}?section=usuarios")
                
                # Validar si el usuario tiene pedidos pendientes o en proceso (Vendedor)
                if usuario_eliminar.rol.nombre_rol == "Vendedor":
                    tiene_pedidos_vendedor = Pedido.objects.filter(
                        detallepedido__prenda__idLocal__IdUsuario=usuario_eliminar,
                        estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
                    ).exists()
                    if tiene_pedidos_vendedor:
                        messages.error(request, f"❌ No se puede eliminar a {usuario_eliminar.nombres} porque tiene pedidos pendientes o en proceso asociados a sus locales.")
                        return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

                # Si todas las validaciones pasan, procedemos a eliminar y guardar para deshacer
                request.session['last_deleted_user'] = {
                    'nombres': usuario_eliminar.nombres,
                    'apellidos': usuario_eliminar.apellidos,
                    'correo': usuario_eliminar.correo,
                    'fecha_nacimiento': str(usuario_eliminar.fecha_nacimiento),
                    'tipo_identificacion': usuario_eliminar.tipo_identificacion,
                    'num_identificacion': usuario_eliminar.num_identificacion,
                    'password': usuario_eliminar.password,
                    'rol_id': usuario_eliminar.rol_id
                }
                usuario_eliminar.delete()
                messages.success(request, f"✅ Usuario <b>{usuario_eliminar.nombres}</b> eliminado correctamente. ¿Deseas deshacer esta acción? <form method='POST' class='inline ml-2'><input type='hidden' name='csrfmiddlewaretoken' value='{get_token(request)}'><input type='hidden' name='accion' value='deshacer'><button type='submit' class='underline font-black uppercase text-emerald-700 hover:text-emerald-900'>[Deshacer]</button></form> <span class='countdown-timer ml-2 opacity-50'>(10s)</span>")
            return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

        elif accion == "deshacer":
            user_data = request.session.get('last_deleted_user')
            if user_data:
                Usuario.objects.create(**user_data)
                del request.session['last_deleted_user']
                messages.success(request, "♻️ Usuario restaurado con éxito.")
                return redirect(f"{reverse('admin_dashboard')}?section=usuarios")
            
            local_data = request.session.get('last_deleted_local')
            if local_data:
                Local.objects.create(**local_data)
                del request.session['last_deleted_local']
                messages.success(request, "♻️ Local restaurado con éxito.")
                return redirect(f"{reverse('admin_dashboard')}?section=locales")

            prenda_data = request.session.get('last_deleted_prenda')
            if prenda_data:
                Prendas.objects.create(**prenda_data)
                del request.session['last_deleted_prenda']
                messages.success(request, "♻️ Uniforme restaurado con éxito.")
                return redirect(f"{reverse('admin_dashboard')}?section=uniformes")
            return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

        elif accion == "cambiar_rol":
            nuevo_rol_id = request.POST.get("rol_id")
            usuario_editar = get_object_or_404(Usuario, id=user_id)
            nuevo_rol = get_object_or_404(Rol, id=nuevo_rol_id)
            
            # --- VALIDACIONES DE NEGOCIO ---
            # 1. Si es Vendedor y tiene pedidos en sus locales
            if usuario_editar.rol.nombre_rol == "Vendedor":
                tiene_pedidos_vendedor = Pedido.objects.filter(
                    detallepedido__prenda__idLocal__IdUsuario=usuario_editar,
                    estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
                ).exists()
                if tiene_pedidos_vendedor:
                    messages.error(request, f"❌ No puedes cambiar el rol de {usuario_editar.nombres}. Tiene locales con pedidos pendientes por entregar.")
                    return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

            # 2. Si es Cliente y tiene pedidos realizados
            if usuario_editar.rol.nombre_rol == "Cliente":
                tiene_pedidos_cliente = Pedido.objects.filter(
                    usuario=usuario_editar,
                    estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
                ).exists()
                if tiene_pedidos_cliente:
                    messages.error(request, f"❌ {usuario_editar.nombres} tiene pedidos en proceso como cliente. Debe finalizarlos antes de cambiar su rol.")
                    return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

            usuario_editar.rol = nuevo_rol
            usuario_editar.save()
            
            # Si el admin se cambia el rol a sí mismo, actualizamos su sesión o lo sacamos
            if str(usuario_editar.id) == str(request.session.get("usuario_id")):
                request.session["usuario_rol"] = nuevo_rol.nombre_rol
                if nuevo_rol.nombre_rol != "Administrador":
                    messages.info(request, "Tu rol ha cambiado. Acceso administrativo revocado.")
                    return redirect("landing")

            messages.success(request, f"✨ El rol de {usuario_editar.nombres} ahora es {nuevo_rol.nombre_rol}.")
            return redirect(f"{reverse('admin_dashboard')}?section=usuarios")

        elif accion == "eliminar_local":
            local_id = request.POST.get("local_id")
            local = get_object_or_404(Local, IdLocal=local_id)
            motivo = request.POST.get("motivo", "").strip() or "No se especificó un motivo."
            
            with transaction.atomic():
                if Pedido.objects.filter(detallepedido__prenda__idLocal=local, estado__estado_pedido__in=['PENDIENTE', 'En Proceso']).exists():
                    messages.error(request, "❌ No se puede eliminar: el local tiene pedidos en curso.")
                else:
                    # Notificar al vendedor antes de borrar el objeto local
                    from locales.models import Notificacion
                    Notificacion.objects.create(
                        usuario=local.IdUsuario,
                        mensaje=f"Tu local '{local.Nombre_local}' ha sido eliminado por la administración.",
                        motivo=motivo,
                        tipo='error'
                    )

                    # Guardar datos para deshacer
                    request.session['last_deleted_local'] = {
                        'IdUsuario_id': local.IdUsuario_id,
                        'Nombre_local': local.Nombre_local,
                        'Descripcion': local.Descripcion,
                        'Ubicacion_direccion': local.Ubicacion_direccion,
                        'Imagen': local.Imagen.name if local.Imagen else None,
                        'Horaapertura': str(local.Horaapertura) if local.Horaapertura else None,
                        'HoraCierre': str(local.HoraCierre) if local.HoraCierre else None,
                        'EstaActivo': local.EstaActivo,
                        'Numero': local.Numero
                    }
                    nombre = local.Nombre_local
                    local.delete()
                    messages.success(request, f"🗑️ Local <b>{nombre}</b> eliminado. ¿Deseas deshacer? <form method='POST' class='inline ml-2'><input type='hidden' name='csrfmiddlewaretoken' value='{get_token(request)}'><input type='hidden' name='accion' value='deshacer'><button type='submit' class='underline font-black uppercase text-emerald-700 hover:text-emerald-900'>[Deshacer]</button></form> <span class='countdown-timer ml-2 opacity-50'>(10s)</span>")
            return redirect(f"{reverse('admin_dashboard')}?section=locales")

        elif accion == "eliminar_prenda":
            prenda_id = request.POST.get("prenda_id")
            prenda = get_object_or_404(Prendas, pk=prenda_id)
            motivo = request.POST.get("motivo", "").strip() or "Incumplimiento de las políticas de la plataforma."
            
            with transaction.atomic():
                # Validación de integridad: No borrar si hay pedidos pendientes que dependan de este ID exacto
                if Pedido.objects.filter(detallepedido__prenda=prenda, estado__estado_pedido__in=['PENDIENTE', 'En Proceso']).exists():
                    messages.error(request, f"❌ No se puede eliminar permanentemente: el uniforme '{prenda.nombre}' tiene pedidos en curso.")
                else:
                    # Notificar al vendedor (Dueño del local)
                    from locales.models import Notificacion
                    Notificacion.objects.create(
                        usuario=prenda.idLocal.IdUsuario,
                        mensaje=f"Tu uniforme '{prenda.nombre}' ha sido eliminado permanentemente por la administración.",
                        motivo=motivo,
                        tipo='error'
                    )

                    # Respaldar en sesión para deshacer
                    request.session['last_deleted_prenda'] = {
                        'idLocal_id': prenda.idLocal_id,
                        'nombre': prenda.nombre,
                        'descripcion': prenda.descripcion,
                        'precio': str(prenda.precio),
                        'talla': prenda.talla,
                        'material': prenda.material,
                        'stock': prenda.stock,
                        'activo': prenda.activo,
                        'tipoPrenda': prenda.tipoPrenda,
                        'imagen': prenda.imagen.name if prenda.imagen else None
                    }
                    nombre = prenda.nombre
                    prenda.delete()
                    messages.success(request, f"🗑️ Uniforme <b>{nombre}</b> eliminado permanentemente. ¿Deseas deshacer? <form method='POST' class='inline ml-2'><input type='hidden' name='csrfmiddlewaretoken' value='{get_token(request)}'><input type='hidden' name='accion' value='deshacer'><button type='submit' class='underline font-black uppercase text-emerald-700 hover:text-emerald-900'>[Deshacer]</button></form> <span class='countdown-timer ml-2 opacity-50'>(10s)</span>")
            return redirect(f"{reverse('admin_dashboard')}?section=uniformes")

        elif accion == "cancelar_pedido":
            pedido_id = request.POST.get("pedido_id")
            motivo = request.POST.get("motivo", "").strip() or "Cancelación por parte del administrador."
            if not pedido_id:
                messages.error(request, "❌ No se proporcionó un ID de pedido válido.")
            else:
                pedido = get_object_or_404(Pedido, idPedido=pedido_id)
                if pedido.estado.estado_pedido in ['COMPLETADO', 'CANCELADO']:
                    messages.warning(request, f"⚠️ El pedido #{pedido_id} ya se encuentra en un estado final ({pedido.estado.estado_pedido}).")
                else:
                    if len(motivo) > 150:
                        messages.error(request, "❌ El motivo de cancelación no puede exceder los 150 caracteres.")
                        return redirect(f"{reverse('admin_dashboard')}?section=pedidos")
                        
                    estado_cancelado, _ = EstadoPedido.objects.get_or_create(estado_pedido='CANCELADO')
                    pedido.estado = estado_cancelado
                    pedido.save()

                    # Notificar al cliente
                    from locales.models import Notificacion
                    Notificacion.objects.create(
                        usuario=pedido.usuario,
                        mensaje=f"Tu pedido #{pedido.idPedido} ha sido cancelado por la administración.",
                        motivo=motivo,
                        tipo='error'
                    )
                    messages.success(request, f"✅ Pedido #{pedido_id} marcado como CANCELADO.")
            return redirect(f"{reverse('admin_dashboard')}?section=pedidos")

    # --- LÓGICA DE DATOS Y FILTROS ---
    q_search = request.GET.get('q_search', '').strip()
    
    # Notificaciones para el Admin
    # Nota: Se filtran pero ya no se mostrarán en el dashboard según requerimiento
    from locales.models import Notificacion 
    notifs = Notificacion.objects.filter(usuario_id=request.session.get("usuario_id")).order_by('-fecha')[:10]

    usuarios, locales, pedidos, uniformes = [], [], [], []
    
    if section == 'usuarios':
        usuarios = Usuario.objects.all().select_related('rol').order_by('-id')
        f_rol = request.GET.get('f_rol', '')
        f_tipo_id = request.GET.get('f_tipo_id', '')
        if q_search:
            usuarios = usuarios.filter(Q(nombres__icontains=q_search) | Q(apellidos__icontains=q_search) | Q(num_identificacion__icontains=q_search) | Q(correo__icontains=q_search))
        if f_rol: usuarios = usuarios.filter(rol_id=f_rol)
        if f_tipo_id: usuarios = usuarios.filter(tipo_identificacion=f_tipo_id)

    elif section == 'locales':
        locales = Local.objects.all().select_related('IdUsuario').order_by('-IdLocal')
        f_status = request.GET.get('f_status', '')
        if q_search:
            locales = locales.filter(Q(Nombre_local__icontains=q_search) | Q(IdUsuario__nombres__icontains=q_search))
        if f_status == '1': locales = locales.filter(EstaActivo=True)
        elif f_status == '0': locales = locales.filter(EstaActivo=False)

    elif section == 'pedidos':
        # Usamos Subquery y Sum para obtener la información detallada que solicitaste
        from django.db.models import OuterRef, Subquery, Sum
        from uniformes.models import DetallePedido

        # Subconsulta para obtener el motivo de la notificación de cancelación si existe
        motivo_subquery = Notificacion.objects.filter(
            mensaje__icontains=OuterRef('idPedido'),
            tipo='error'
        ).values('motivo')[:1]

        detalles_qs = DetallePedido.objects.filter(pedido=OuterRef('pk'))
        primer_local = detalles_qs.values('prenda__idLocal__Nombre_local')[:1]
        primer_uniforme = detalles_qs.values('prenda__nombre')[:1]
        
        pedidos = Pedido.objects.all().select_related('usuario', 'estado').annotate(
            local_nombre=Subquery(primer_local),
            uniforme_nombre=Subquery(primer_uniforme),
            motivo_cancelacion=Subquery(motivo_subquery),
            cantidad_total=Sum('detallepedido__cantidad'),
            precio_total=Sum('detallepedido__total_pedido')
        ).order_by('-idPedido')
        
        f_estado = request.GET.get('f_estado', '')
        if q_search:
            pedidos = pedidos.filter(Q(idPedido__icontains=q_search) | Q(usuario__nombres__icontains=q_search) | Q(detallepedido__prenda__idLocal__Nombre_local__icontains=q_search)).distinct()
        if f_estado:
            pedidos = pedidos.filter(estado__estado_pedido=f_estado)

    elif section == 'uniformes':
        uniformes = Prendas.objects.all().select_related('idLocal', 'idLocal__IdUsuario').order_by('-idPrenda')
        f_talla = request.GET.get('f_talla', '')
        f_material = request.GET.get('f_material', '')
        if q_search:
            uniformes = uniformes.filter(Q(nombre__icontains=q_search) | Q(idPrenda__icontains=q_search) | Q(idLocal__Nombre_local__icontains=q_search))
        if f_talla: uniformes = uniformes.filter(talla=f_talla)
        if f_material: uniformes = uniformes.filter(material=f_material)

    return render(request, "dashadmin.html", {
        "nombre": request.session.get("usuario_nombre"),
        "section": section,
        "usuarios": usuarios,
        "locales": locales,
        "pedidos": pedidos,
        "uniformes": uniformes,
        "roles": Rol.objects.all(),
        "notificaciones": notifs,
        "estados_pedido": EstadoPedido.ESTADO_CHOICES,
        "tipo_identificacion_choices": Usuario.TIPOS_IDENTIFICACION,
        "q_search": q_search,
        "f_rol_sel": request.GET.get('f_rol', ''),
        "f_tipo_id_sel": request.GET.get('f_tipo_id', ''),
        "f_status_sel": request.GET.get('f_status', ''),
        "f_estado_sel": request.GET.get('f_estado', ''),
        "f_talla_sel": request.GET.get('f_talla', ''),
        "f_material_sel": request.GET.get('f_material', ''),
        "talla_choices": Prendas.TALLA_CHOICES,
        "material_choices": Prendas.MATERIAL_CHOICES,
    })

@never_cache
def politicas(request):
    return render(request, "politicas.html")
