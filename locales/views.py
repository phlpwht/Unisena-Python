from uniformes.models import Prendas, Pedido, DetallePedido, EstadoPedido

from django.shortcuts import render, redirect, get_object_or_404
from .models import Local
from usuario.models import Usuario  #ajusta el import según tu app
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from inventario.models import MovimientoInventario
from allauth.socialaccount.models import SocialAccount

def lista_locales(request):
    if "usuario_id" not in request.session:
        return redirect("login")
    
    usuario_id = request.session.get("usuario_id")
    usuario_rol = request.session.get("usuario_rol")

    if usuario_rol == "Vendedor":
        # Los vendedores ven sus propios locales (activos e inactivos)
        locales = Local.objects.filter(IdUsuario_id=usuario_id)
        modo = 'crud'
    elif usuario_rol == "Administrador":
        # El admin ve todo
        locales = Local.objects.all()
        modo = 'crud'
    else:
        # Los clientes SOLO ven los locales que están ACTIVOS
        locales = Local.objects.filter(EstaActivo=True)
        modo = 'ver'

    total_propios = Local.objects.filter(IdUsuario_id=usuario_id).count()
    puede_crear = total_propios < 3 and usuario_rol == "Vendedor"

    return render(request, 'lista.html', { #AQUÍ PASAMOS LOS LOCALES FILTRADOS AL TEMPLATE
        'locales': locales,
        'modo': modo,
        'puede_crear': puede_crear
    })


def crear_local(request):
    if request.method == 'POST':

        usuario_id = request.session.get("usuario_id")
        total_locales = Local.objects.filter(IdUsuario_id=usuario_id).count()

        if total_locales >= 3:
            messages.error(request, "Solo puedes registrar máximo 3 locales ❌")
            return redirect('lista_locales')

        Local.objects.create(
            IdUsuario_id=usuario_id,
            Nombre_local=request.POST.get('Nombre_local'),
            Descripcion=request.POST.get('Descripcion'),
            Ubicacion_direccion=request.POST.get('Ubicacion_direccion'),
            Imagen=request.FILES.get('Imagen'),
            Horaapertura = request.POST.get('Horaapertura') or None,
            HoraCierre = request.POST.get('HoraCierre') or None
        )

        messages.success(request, "Local creado correctamente 🎉")
        return redirect('lista_locales')
    return render(request, 'formulario.html')


def editar_local(request, id):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    local = get_object_or_404(Local, IdLocal=id, IdUsuario_id=usuario_id)
    if request.method == 'POST':
        local.Nombre_local = request.POST.get('Nombre_local')
        local.Descripcion = request.POST.get('Descripcion')
        local.Ubicacion_direccion = request.POST.get('Ubicacion_direccion')
        if request.FILES.get('Imagen'):
            local.Imagen = request.FILES.get('Imagen')
        hora_apertura = request.POST.get('Horaapertura')
        hora_cierre = request.POST.get('HoraCierre')

        local.Horaapertura = hora_apertura if hora_apertura else None
        local.HoraCierre = hora_cierre if hora_cierre else None

        local.save()
        messages.success(request, "Local actualizado correctamente ✨")
        return redirect('lista_locales')
    return render(request, 'formulario.html', {'local': local})


def eliminar_local(request, id):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    usuario = get_object_or_404(Usuario, id=usuario_id)
    local = get_object_or_404(Local, IdLocal=id, IdUsuario_id=usuario_id)

    # 🚨 VALIDACIÓN: No permitir eliminar si hay pedidos pendientes
    if Pedido.objects.filter(detallepedido__prenda__idLocal=local, estado__estado_pedido__in=['PENDIENTE', 'PROCESO']).exists():
        messages.error(request, "No se puede eliminar: el local tiene pedidos pendientes.")
        return redirect('lista_locales')


    if request.method == 'POST':
        nombre_confirmacion = request.POST.get('nombre_confirmacion')

        if nombre_confirmacion == local.Nombre_local:
            nombre_local = local.Nombre_local
            local.delete()
            
            # Enviar correo de notificación por eliminación
            asunto = f"🛑 Local Eliminado: {nombre_local}"
            mensaje_texto = f"Hola {usuario.nombres}, te confirmamos que el local '{nombre_local}' ha sido eliminado de nuestra plataforma."
            
            mensaje_html = f"""
            <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <div style="background-color: #ef4444; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">Local Eliminado</h1>
                    </div>
                    <div style="padding: 30px; line-height: 1.6; color: #333;">
                        <p style="font-size: 18px;">Hola <strong>{usuario.nombres}</strong>,</p>
                        <p>Te confirmamos que el local <strong>{nombre_local}</strong> ha sido eliminado definitivamente de nuestra plataforma.</p>
                        <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 15px; margin: 20px 0;">
                            <p style="margin: 0; color: #991b1b; font-weight: bold;">⚠️ Acción Irreversible</p>
                            <p style="margin: 5px 0 0 0; color: #b91c1c; font-size: 14px;">Todos los datos, uniformes e historial asociados a este local han sido borrados de forma permanente.</p>
                        </div>
                        <p>Si no realizaste esta acción, por favor contacta a nuestro equipo de seguridad de inmediato.</p>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="margin: 0; color: #64748b; font-size: 12px;">© 2026 UniSena - Plataforma de Gestión de Uniformes</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            try:
                email = EmailMultiAlternatives(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.correo]
                )
                email.attach_alternative(mensaje_html, "text/html")
                email.send()
            except Exception as e:
                print(f"🚨 Error enviando correo de eliminación: {e}")

            messages.success(request, "Local eliminado con éxito.")
        
        else:
            messages.error(request, "El nombre no coincide.")
            
        return redirect('lista_locales')
    return redirect('lista_locales')


def dashboard_vendedor(request):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    total_locales = Local.objects.filter(IdUsuario_id=usuario_id).count()
    puede_crear = total_locales < 3
    return render(request, 'dashboard.html', {
        'total_locales': total_locales,
        'puede_crear': puede_crear
    })


def administrar_locales(request):
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session.get("usuario_id")
    
    # Filtramos los locales del vendedor actual
    locales = Local.objects.filter(IdUsuario_id=usuario_id)

    # Volvemos al modo 'ver' y desactivamos la opción de crear para esta vista específica
    return render(request, 'lista.html', {
        'locales': locales,
        'modo': 'ver',
        'puede_crear': False
    })


def detalle_local(request, id):
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session.get("usuario_id")
    usuario_rol = request.session.get("usuario_rol")

    # 🛡️ Seguridad: Si es cliente, el local DEBE estar activo
    if usuario_rol == "Cliente":
        local = get_object_or_404(Local, IdLocal=id, EstaActivo=True)
    elif usuario_rol == "Vendedor":
        # El vendedor puede ver su local aunque esté desactivado
        local = get_object_or_404(Local, IdLocal=id, IdUsuario_id=usuario_id)
    else:
        # Admin
        local = get_object_or_404(Local, IdLocal=id)

    # --- Lógica de Filtrado y Ordenamiento ---
    prendas = Prendas.objects.filter(idLocal=local) # Base de la consulta

    # Filtro por nombre/descripción
    search_query = request.GET.get('search', '').strip()
    if search_query:
        prendas = prendas.filter(
            models.Q(nombre__icontains=search_query) | 
            models.Q(descripcion__icontains=search_query)
        )

    # Filtro por talla
    talla_filter = request.GET.get('talla', '').strip()
    if talla_filter and talla_filter != 'all':
        prendas = prendas.filter(talla=talla_filter)

    # Filtro por material
    material_filter = request.GET.get('material', '').strip()
    if material_filter:
        prendas = prendas.filter(material__icontains=material_filter)

    # Filtro por tipo de prenda
    tipo_prenda_filter = request.GET.get('tipoPrenda', '').strip()
    if tipo_prenda_filter and tipo_prenda_filter != 'all':
        prendas = prendas.filter(tipoPrenda=tipo_prenda_filter)

    # Ordenamiento
    sort_by = request.GET.get('sort', '').strip()
    if sort_by == 'price_asc':
        prendas = prendas.order_by('precio')
    elif sort_by == 'price_desc':
        prendas = prendas.order_by('-precio')
    elif sort_by == 'stock_asc':
        prendas = prendas.order_by('stock')
    elif sort_by == 'stock_desc':
        prendas = prendas.order_by('-stock')
    # --- Fin Lógica de Filtrado y Ordenamiento ---

    mostrar_inventario = request.GET.get('inventario', '0') == '1'

    # 👇 SECCIÓN DE PEDIDOS (BÁSICO)
    mostrar_pedidos = request.GET.get('pedidos', '0') == '1'
    pedidos_local = []

    # Capturamos parámetros de filtro para pedidos
    p_estado = request.GET.get('p_estado', '')
    p_cliente = request.GET.get('p_cliente', '').strip()
    p_fecha_inicio = request.GET.get('p_fecha_inicio', '')
    p_fecha_fin = request.GET.get('p_fecha_fin', '')
    p_id = request.GET.get('p_id', '')

    if mostrar_pedidos:
        pedidos_local = Pedido.objects.filter(
            detallepedido__prenda__idLocal=local
        ).distinct().select_related('estado', 'usuario')

        if p_estado:
            pedidos_local = pedidos_local.filter(estado__estado_pedido=p_estado)
        if p_cliente:
            pedidos_local = pedidos_local.filter(
                models.Q(usuario__nombres__icontains=p_cliente) | 
                models.Q(usuario__apellidos__icontains=p_cliente)
            )
        if p_fecha_inicio:
            pedidos_local = pedidos_local.filter(fecha_pedido__date__gte=p_fecha_inicio)
        if p_fecha_fin:
            pedidos_local = pedidos_local.filter(fecha_pedido__date__lte=p_fecha_fin)
        if p_id:
            pedidos_local = pedidos_local.filter(idPedido=p_id)

        pedidos_local = pedidos_local.order_by('-fecha_pedido')

    # 👇 EDITAR
    prenda_editar = None
    if request.GET.get("editar"):
        prenda_editar = get_object_or_404(Prendas, pk=request.GET.get("editar"))

    # 👇 CREAR (NUEVO)
    mostrar_formulario = request.GET.get("crear") == "1"

    # 👇 SECCIÓN DE MOVIMIENTOS (TIPO INVENTARIO COMPLETO)
    mostrar_movimientos = request.GET.get('movimientos', '0') == '1'
    movimientos_local = []
    resumen_movimientos = {}

    if mostrar_movimientos:
        movimientos_local = MovimientoInventario.objects.filter(idPrenda__idLocal=local)

        # Filtros Multi-criterio Movimientos
        m_inicio = request.GET.get('m_inicio')
        m_fin = request.GET.get('m_fin')
        m_tipo = request.GET.get('m_tipo')
        m_prenda_id = request.GET.get('m_prenda')

        if m_inicio: movimientos_local = movimientos_local.filter(fecha__date__gte=m_inicio)
        if m_fin: movimientos_local = movimientos_local.filter(fecha__date__lte=m_fin)
        if m_tipo: movimientos_local = movimientos_local.filter(tipoMovimiento=m_tipo)
        if m_prenda_id: movimientos_local = movimientos_local.filter(idPrenda_id=m_prenda_id)

        # Reporte de Movimientos
        resumen_movimientos = movimientos_local.aggregate(
            entradas=models.Sum('cantidad', filter=models.Q(tipoMovimiento='ENTRADA')),
            salidas=models.Sum('cantidad', filter=models.Q(tipoMovimiento='SALIDA'))
        )
        movimientos_local = movimientos_local.select_related('idPrenda').order_by('-fecha')

    # Datos para los selectores de filtros
    context_filtros = {
        'm_inicio': request.GET.get('m_inicio', ''),
        'm_fin': request.GET.get('m_fin', ''),
        'm_tipo_sel': request.GET.get('m_tipo', ''),
        'm_prenda_sel': request.GET.get('m_prenda', ''),
    }

    filtros_activos = any([
        search_query, talla_filter != 'all', material_filter, tipo_prenda_filter != 'all', sort_by,
        p_estado, p_cliente, p_fecha_inicio, p_fecha_fin, p_id
    ])

    return render(request, 'detallelocal.html', {
        'local': local,
        'prendas': prendas,
        'mostrar_inventario': mostrar_inventario,
        # Pasamos los valores de los filtros para que se mantengan en el formulario
        'search_query': search_query,
        'talla_filter': talla_filter,
        'material_filter': material_filter,
        'tipo_prenda_filter': tipo_prenda_filter,
        'sort_by': sort_by,
        'prenda_talla_choices': Prendas.TALLA_CHOICES,
        'prenda_tipo_choices': Prendas.TIPO_PRENDA_CHOICES,
        'prenda': prenda_editar,
        'mostrar_formulario': mostrar_formulario,
        'mostrar_pedidos': mostrar_pedidos,
        'mostrar_movimientos': mostrar_movimientos,
        'pedidos_local': pedidos_local,
        'movimientos_local': movimientos_local,
        'resumen_movimientos': resumen_movimientos,
        'filtros_activos': filtros_activos,
        'estados_pedido': EstadoPedido.ESTADO_CHOICES,
        'p_estado_sel': p_estado,
        'p_cliente_search': p_cliente,
        'p_fecha_inicio': p_fecha_inicio,
        'p_fecha_fin': p_fecha_fin,
        'p_id_search': p_id,
        **context_filtros
    })

def toggle_activo_local(request, id):
    if "usuario_id" not in request.session:
        return redirect("login")
    
    usuario_id = request.session.get("usuario_id")
    usuario = get_object_or_404(Usuario, id=usuario_id)
    local = get_object_or_404(Local, IdLocal=id, IdUsuario_id=usuario_id)

    if request.method == 'POST':
        nuevo_estado = not local.EstaActivo

        # 🚨 VALIDACIÓN: No permitir desactivar si hay pedidos pendientes o en proceso
        if not nuevo_estado and Pedido.objects.filter(detallepedido__prenda__idLocal=local, estado__estado_pedido__in=['PENDIENTE', 'PROCESO']).exists():
            messages.error(request, "No se puede desactivar: hay pedidos pendientes.")
            return redirect('lista_locales')

        nombre_confirmacion = request.POST.get('nombre_confirmacion')

        if nombre_confirmacion == local.Nombre_local:
            local.EstaActivo = nuevo_estado
            local.save()
            
            estado_str = "Activado" if nuevo_estado else "Desactivado"
            color_header = "#125f58" if nuevo_estado else "#f59e0b"
            
            # Enviar Correo de Notificación
            asunto = f"⚠️ Notificación de Local: {local.Nombre_local}"
            mensaje_texto = f"Hola {usuario.nombres}, tu local '{local.Nombre_local}' ha sido {estado_str.lower()}."
            
            mensaje_html = f"""
            <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <div style="background-color: {color_header}; padding: 20px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 24px;">Estado de Local Actualizado</h1>
                    </div>
                    <div style="padding: 30px; line-height: 1.6; color: #333;">
                        <p style="font-size: 18px;">Hola <strong>{usuario.nombres}</strong>,</p>
                        <p>Tu local <strong>{local.Nombre_local}</strong> ha cambiado su estado a:</p>
                        <div style="text-align: center; margin: 25px 0;">
                            <span style="background-color: {color_header}; color: white; padding: 10px 25px; border-radius: 50px; font-weight: bold; font-size: 20px; text-transform: uppercase;">
                                {estado_str}
                            </span>
                        </div>
                        <p style="color: #64748b; font-size: 14px;">
                            {"Ahora tus productos son visibles para los clientes." if nuevo_estado else "Tu local y productos han sido ocultados temporalmente de la vista pública."}
                        </p>
                        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 25px 0;">
                        <p style="font-size: 13px; color: #94a3b8;">Si no reconoces esta actividad, te recomendamos cambiar tu contraseña y revisar la seguridad de tu cuenta.</p>
                    </div>
                    <div style="background-color: #f8fafc; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                        <p style="margin: 0; color: #64748b; font-size: 12px;">© 2026 UniSena - Plataforma de Gestión de Uniformes</p>
                    </div>
                </div>
            </body>
            </html>
            """

            try:
                email = EmailMultiAlternatives(
                    asunto,
                    mensaje_texto,
                    settings.DEFAULT_FROM_EMAIL, # 👈 Consistencia en el remitente
                    [usuario.correo]
                )
                email.attach_alternative(mensaje_html, "text/html")
                email.send()
            except Exception as e:
                print(f"🚨 Error enviando correo de cambio de estado: {e}")

            messages.success(request, f"Local {estado_str.lower()} correctamente.")
        else:
            messages.error(request, "El nombre no coincide.")
            
        return redirect('lista_locales')
    
    return redirect('lista_locales')

def ver_movimientos_prenda(request, id_prenda):
    if request.session.get("usuario_rol") != "Vendedor":
        return redirect('landing')
    
    prenda = get_object_or_404(Prendas, pk=id_prenda)
    movimientos = MovimientoInventario.objects.filter(idPrenda=prenda).order_by('-fecha')
    
    return render(request, "movimiento.html", {"prenda": prenda, "movimientos": movimientos})

def detalle_pedido_vendedor(request, id_local, id_pedido):
    """Vista simple para ver el detalle de un pedido específico del local"""
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session.get("usuario_id")
    usuario_rol = request.session.get("usuario_rol")

    if usuario_rol == "Administrador":
        local = get_object_or_404(Local, IdLocal=id_local)
    elif usuario_rol == "Vendedor":
        local = get_object_or_404(Local, IdLocal=id_local, IdUsuario_id=usuario_id)
    else:
        return redirect('landing')

    # Primero obtenemos el pedido por su ID de forma limpia
    pedido = get_object_or_404(Pedido.objects.select_related('estado'), idPedido=id_pedido)
    
    # Verificamos por seguridad que el pedido contenga al menos un producto de este local
    if not DetallePedido.objects.filter(pedido=pedido, prenda__idLocal=local).exists():
        messages.error(request, "No tienes permiso para gestionar este pedido.")
        return redirect('landing')
    
    if request.method == "POST":
        nuevo_estado_val = request.POST.get("nuevo_estado")
        if nuevo_estado_val:
            # Normalizamos a mayúsculas para evitar duplicados inconsistentes en la DB
            estado_obj, _ = EstadoPedido.objects.get_or_create(estado_pedido=nuevo_estado_val.strip().upper())
            pedido.estado = estado_obj
            pedido.save()
            messages.success(request, f"✅ Estado de la orden actualizado a {nuevo_estado_val}")
            return redirect('detalle_pedido_vendedor', id_local=local.IdLocal, id_pedido=pedido.idPedido)

    detalles = DetallePedido.objects.filter(pedido=pedido, prenda__idLocal=local)
    
    totales = detalles.aggregate(
        total=models.Sum('total_pedido'),
        abono=models.Sum('total_abono')
    )
    
    return render(request, "detalle_pedido_vendedor.html", {
        "pedido": pedido, 
        "detalles": detalles, 
        "local": local,
        "total_venta_local": totales['total'] or 0,
        "total_abono_local": totales['abono'] or 0,
        "estados_pedido": EstadoPedido.ESTADO_CHOICES
    })
