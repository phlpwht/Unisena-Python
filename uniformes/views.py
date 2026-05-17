import os, json
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from .models import Prendas, Pedido, DetallePedido, EstadoPedido
from locales.models import Local
from decimal import Decimal
from django.contrib import messages
from django.db import models, transaction
import pandas as pd
import io
from django.http import JsonResponse
from django.urls import reverse
from django.core.files import File
from django.db.models import OuterRef, Subquery
from inventario.models import MovimientoInventario
from .models import CalificacionPedido

def crear_prenda(request, id_local):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    local = get_object_or_404(Local, pk=id_local, IdUsuario_id=usuario_id)

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        talla = request.POST.get("talla")
        material = request.POST.get("material")
        tipo_prenda = request.POST.get("tipoPrenda")
        imagen = request.FILES.get("imagen")

        errores = []

        # Validación de imagen
        if not imagen:
            errores.append("❌ La imagen es obligatoria")

        # Validación de precio
        try:
            precio_decimal = Decimal(precio)
            if precio_decimal <= 0:
                errores.append("❌ El precio debe ser mayor a 0 COP 💰")
        except:
            errores.append("❌ Precio inválido")

        # Validación de stock
        try:
            stock_int = int(stock)
            if stock_int <= 0:
                errores.append("❌ El stock debe ser mayor a 0 📦")
        except:
            errores.append("❌ Stock inválido")

        if errores:
            for error in errores:
                messages.error(request, error)
            prendas = Prendas.objects.filter(idLocal=local)
            # Renderizar plantilla completa para mantener formulario abierto
            return render(request, "detallelocal.html", {
                "local": local,
                "prendas": prendas,
                "prenda": request.POST, # 👈 Devolvemos lo que el usuario escribió
                "mostrar_formulario": True,
                "prenda_talla_choices": Prendas.TALLA_CHOICES,
                "prenda_material_choices": Prendas.MATERIAL_CHOICES,
                "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
            })

        # Crear la prenda si todo es válido
        try:
            nueva_prenda = Prendas.objects.create(
                idLocal=local,
                nombre=nombre,
                descripcion=descripcion,
                precio=precio_decimal,
                stock=stock_int,
                talla=talla,
                material=material,
                tipoPrenda=tipo_prenda,
                imagen=imagen,
            )

            # Registrar el movimiento de entrada en el inventario
            MovimientoInventario.objects.create(
                idPrenda=nueva_prenda,
                tipoMovimiento='ENTRADA',
                cantidad=stock_int
            )

            messages.success(request, "✅ Prenda creada correctamente")
            return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")
        except Exception as e:
            messages.error(request, f"❌ Error al crear prenda: {e}")
            prendas = Prendas.objects.filter(idLocal=local)
            return render(request, "detallelocal.html", {
                "local": local,
                "prendas": prendas,
                "prenda": request.POST,
                "mostrar_formulario": True,
                "prenda_talla_choices": Prendas.TALLA_CHOICES,
                "prenda_material_choices": Prendas.MATERIAL_CHOICES,
                "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
            })

    return render(request, "detallelocal.html", {"local": local})


def editar_prenda(request, id_prenda):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    prenda = get_object_or_404(Prendas, pk=id_prenda, idLocal__IdUsuario_id=usuario_id)
    local = prenda.idLocal

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descripcion = request.POST.get("descripcion")
        precio = request.POST.get("precio")
        stock = request.POST.get("stock")
        talla = request.POST.get("talla")
        material = request.POST.get("material")
        tipo_prenda = request.POST.get("tipoPrenda")
        imagen = request.FILES.get("imagen")  # nueva imagen opcional

        errores = []

        # Validación de precio
        try:
            precio_decimal = Decimal(precio)
            if precio_decimal <= 0:
                errores.append("❌ El precio debe ser mayor a 0 COP 💰")
        except:
            errores.append("❌ Precio inválido")

        # Validación de stock
        try:
            stock_int = int(stock)
            if stock_int <= 0:
                errores.append("❌ El stock debe ser mayor a 0 📦")
        except:
            errores.append("❌ Stock inválido")

        # Validación de imagen solo si no tiene imagen previa
        if not prenda.imagen and not imagen:
            errores.append("❌ La imagen es obligatoria")

        if errores:
            for error in errores:
                messages.error(request, error)
            
            # Actualizamos el objeto con los datos del POST para que el formulario los muestre
            prenda.nombre = nombre
            prenda.descripcion = descripcion
            prenda.talla = talla
            prenda.material = material
            prenda.tipoPrenda = tipo_prenda
            # Nota: No actualizamos precio/stock aquí si fallaron la conversión, 
            # pero el formulario usará el valor previo o el fallido según la lógica del template.

            prendas = Prendas.objects.filter(idLocal=local)
            return render(request, "detallelocal.html", {
                "local": local,
                "prendas": prendas,
                "prenda": prenda,
                "mostrar_formulario": True,
                "prenda_talla_choices": Prendas.TALLA_CHOICES,
                "prenda_material_choices": Prendas.MATERIAL_CHOICES,
                "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
            })

        # Guardar cambios
        prenda.nombre = nombre
        prenda.descripcion = descripcion
        prenda.precio = precio_decimal
        prenda.stock = stock_int
        prenda.talla = talla
        prenda.material = material
        prenda.tipoPrenda = tipo_prenda
        if imagen:
            prenda.imagen = imagen
        
        # Si se añade stock a un producto agotado, se reactiva automáticamente
        if prenda.stock > 0:
            prenda.activo = True

        try:
            prenda.save()
            messages.success(request, "Prenda editada correctamente ✨")
            return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")
        except Exception as e:
            messages.error(request, f"❌ Error al editar prenda: {e}")
            prendas = Prendas.objects.filter(idLocal=local)
            return render(request, "detallelocal.html", {
                "local": local,
                "prendas": prendas,
                "prenda": prenda,
                "mostrar_formulario": True,
                "prenda_talla_choices": Prendas.TALLA_CHOICES,
                "prenda_material_choices": Prendas.MATERIAL_CHOICES,
                "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
            })

    # Si se accede por GET, redirige a la página con formulario en modo edición
    return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?editar={prenda.idPrenda}")


def eliminar_prenda(request, id_prenda):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    prenda = get_object_or_404(Prendas, pk=id_prenda, idLocal__IdUsuario_id=usuario_id)
    local = prenda.idLocal

    try:
        if request.method == "POST":
            cantidad_eliminar = int(request.POST.get('cantidad_eliminar', 0))

            # 🚨 VALIDACIÓN: Verificar unidades comprometidas en pedidos activos
            unidades_reservadas = DetallePedido.objects.filter(
                prenda=prenda,
                pedido__estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
            ).aggregate(total=models.Sum('cantidad'))['total'] or 0

            if cantidad_eliminar == 0 or cantidad_eliminar >= prenda.stock:
                # Eliminación lógica: ponemos stock en 0 y desactivamos
                if unidades_reservadas > 0:
                    messages.error(request, f"❌ No se puede eliminar el producto: hay {unidades_reservadas} unidades reservadas en pedidos pendientes.")
                    return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")
                
                prenda.stock = 0
                prenda.activo = False
                prenda.save()
                messages.success(request, "✅ Producto eliminado del inventario por falta de stock.")
            elif cantidad_eliminar > 0:
                # Eliminación parcial (ajuste de stock)
                if (prenda.stock - cantidad_eliminar) < unidades_reservadas:
                    messages.error(request, f"⚠️ No puedes retirar {cantidad_eliminar} unidades. Debes dejar al menos {unidades_reservadas} para cubrir pedidos pendientes.")
                    return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")

                prenda.stock -= cantidad_eliminar
                if prenda.stock <= 0:
                    prenda.stock = 0
                    prenda.activo = False
                prenda.save()

                # Registrar el movimiento de salida en el inventario
                MovimientoInventario.objects.create(
                    idPrenda=prenda,
                    tipoMovimiento='SALIDA',
                    cantidad=cantidad_eliminar
                )

                messages.success(request, f"✅ Se eliminaron {cantidad_eliminar} unidades del stock.")
            else:
                # Eliminación lógica por defecto
                prenda.stock = 0
                prenda.activo = False
                prenda.save()
                messages.success(request, "✅ Prenda eliminada correctamente")
        else:
            return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")
    except Exception as e:
        messages.error(request, f"❌ Error al eliminar la prenda: {e}")

    return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")


def bulk_upload_prendas(request, id_local):
    if "usuario_id" not in request.session:
        return redirect("login")
    usuario_id = request.session.get("usuario_id")
    local = get_object_or_404(Local, pk=id_local, IdUsuario_id=usuario_id)

    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, "❌ No se ha seleccionado ningún archivo.")
            return render(request, 'bulk_upload_form.html', {'local': local})

        file = request.FILES['file']
        if not file.name.endswith(('.csv', '.xlsx')):
            messages.error(request, "❌ Formato de archivo no válido. Solo se permiten .csv o .xlsx.")
            return render(request, 'bulk_upload_form.html', {'local': local})

        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(io.StringIO(file.read().decode('utf-8')))
            else: # .xlsx
                df = pd.read_excel(file)

            # Columnas esperadas (asegúrate de que coincidan con tu modelo)
            expected_columns = ['nombre', 'descripcion', 'precio', 'stock', 'talla', 'material', 'tipoPrenda']
            if not all(col in df.columns for col in expected_columns):
                messages.error(request, f"❌ El archivo debe contener las columnas: {', '.join(expected_columns)}")
                return render(request, 'bulk_upload_form.html', {'local': local})

            prendas_creadas = 0
            errores_fila = []

            for index, row in df.iterrows():
                try:
                    nombre = str(row['nombre']).strip()
                    descripcion = str(row['descripcion']).strip()
                    precio = Decimal(str(row['precio']).replace(',', '.').strip()) # Manejar comas como separador decimal
                    stock = int(str(row['stock']).strip())
                    talla = str(row['talla']).replace(' ', '').strip().upper()
                    
                    # Mapeo para material
                    mat_raw = str(row['material']).strip().lower()
                    material = 'Algodon' if 'algodon' in mat_raw or 'algodón' in mat_raw else 'Malla' if 'malla' in mat_raw else mat_raw.capitalize()
                    
                    # Mapeo inteligente para tipo de prenda
                    tipo_raw = str(row['tipoPrenda']).strip().lower()
                    if 'completa' in tipo_raw:
                        tipo_prenda = 'completa'
                    elif 'unidad' in tipo_raw:
                        tipo_prenda = 'unidad'
                    else:
                        tipo_prenda = tipo_raw

                    # Validaciones básicas
                    if not nombre:
                        raise ValueError("El nombre no puede estar vacío.")
                    if precio <= 0:
                        raise ValueError("El precio debe ser mayor a 0.")
                    if stock <= 0:
                        raise ValueError("El stock debe ser mayor a 0.")
                    if talla not in [choice[0] for choice in Prendas.TALLA_CHOICES]: # Asumiendo que tienes TALLA_CHOICES en tu modelo
                        tallas_validas = ", ".join([choice[0] for choice in Prendas.TALLA_CHOICES])
                        raise ValueError(f"Talla '{talla}' no válida. Opciones: {tallas_validas}.")
                    if material not in [choice[0] for choice in Prendas.MATERIAL_CHOICES]:
                        mats_validos = " o ".join([choice[0] for choice in Prendas.MATERIAL_CHOICES])
                        raise ValueError(f"Material '{material}' no válido. Los únicos materiales permitidos son: {mats_validos}.")
                    if tipo_prenda not in [choice[0] for choice in Prendas.TIPO_PRENDA_CHOICES]: # Asumiendo que tienes TIPO_PRENDA_CHOICES
                        tipos_validos = ", ".join([choice[0] for choice in Prendas.TIPO_PRENDA_CHOICES])
                        raise ValueError(f"Tipo de prenda '{tipo_prenda}' no válido. Opciones: {tipos_validos}.")

                    # Crear objeto sin guardar aún para procesar imagen si existe
                    nueva_prenda = Prendas(
                        idLocal=local,
                        nombre=nombre,
                        descripcion=descripcion,
                        precio=precio,
                        stock=stock,
                        talla=talla,
                        material=material,
                        tipoPrenda=tipo_prenda
                    )

                    # 🖼️ Lógica de Imagen Local (Opcional)
                    # El usuario debe crear una columna 'imagen_local' con la ruta: C:\fotos\img.jpg
                    if 'imagen_local' in df.columns:
                        ruta_foto = str(row['imagen_local']).strip()
                        if ruta_foto and os.path.exists(ruta_foto):
                            try:
                                with open(ruta_foto, 'rb') as f:
                                    nombre_archivo = os.path.basename(ruta_foto)
                                    nueva_prenda.imagen.save(nombre_archivo, File(f), save=False)
                            except Exception as img_e:
                                errores_fila.append(f"Fila {index + 2}: Error al leer la imagen en {ruta_foto}")

                    nueva_prenda.save()

                    # Registrar el movimiento de entrada en el inventario por carga masiva
                    MovimientoInventario.objects.create(
                        idPrenda=nueva_prenda,
                        tipoMovimiento='ENTRADA',
                        cantidad=stock
                    )

                    prendas_creadas += 1
                except Exception as e:
                    errores_fila.append(f"Fila {index + 2}: {e}") # +2 porque pandas es 0-indexed y la primera fila es el encabezado
            
            if prendas_creadas > 0:
                messages.success(request, f"✅ Se crearon {prendas_creadas} prendas correctamente.")
            if errores_fila:
                for error in errores_fila:
                    messages.error(request, f"⚠️ Error en carga masiva: {error}")
                messages.info(request, "Algunas prendas no pudieron ser creadas. Revisa los errores detallados arriba.")
            
            if prendas_creadas == 0 and not errores_fila:
                messages.warning(request, "No se encontraron prendas válidas para crear en el archivo.")

            return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")

        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")
            return render(request, "bulk_upload_form.html", {"local": local})

    return render(request, "bulk_upload_form.html", {"local": local})


def eliminar_prendas_masivo(request, id_local):
    if "usuario_id" not in request.session:
        return redirect("login")

    usuario_id = request.session.get("usuario_id")
    local = get_object_or_404(Local, pk=id_local, IdUsuario_id=usuario_id)

    if request.method == "POST":
        ids = request.POST.getlist("prendas_ids")
        if not ids:
            messages.warning(request, "⚠️ No seleccionaste ninguna prenda.")
        else:
            try:
                # Filtrar qué IDs de los seleccionados tienen pedidos pendientes
                ids_con_pedidos = DetallePedido.objects.filter(
                    prenda_id__in=ids,
                    pedido__estado__estado_pedido__in=['PENDIENTE', 'En Proceso']
                ).values_list('prenda_id', flat=True).distinct()

                # Solo permitimos eliminar los que NO estén en esa lista
                ids_a_eliminar = [int(i) for i in ids if int(i) not in ids_con_pedidos]
                
                cant_eliminadas = Prendas.objects.filter(idPrenda__in=ids_a_eliminar, idLocal=local).update(activo=False, stock=0)
                
                if len(ids_con_pedidos) > 0:
                    messages.warning(request, f"⚠️ Se eliminaron {cant_eliminadas} prendas, pero {len(ids_con_pedidos)} no se pudieron borrar por tener pedidos pendientes.")
                else:
                    messages.success(request, f"✅ Se eliminaron {cant_eliminadas} prendas correctamente.")
            except Exception as e:
                messages.error(request, f"❌ Error al eliminar prendas: {e}")

    return redirect(f"{reverse('detalle_local', args=[local.IdLocal])}?inventario=1")

def catalogo_prendas(request):
    nombre = request.session.get("usuario_nombre")
    rol = request.session.get("usuario_rol")
    usuario_id = request.session.get("usuario_id")

    # Solo prendas de locales activos
    prendas_qs = Prendas.objects.filter(idLocal__EstaActivo=True, activo=True).select_related('idLocal', 'idLocal__IdUsuario')

    # Alerta persistente
    pedidos_pendientes_count = Pedido.objects.filter(
        usuario_id=usuario_id,
        estado__estado_pedido='PENDIENTE'
    ).count()

    # --- FILTROS ---
    search_prenda = request.GET.get('search_prenda', '').strip()
    if search_prenda:
        prendas_qs = prendas_qs.filter(nombre__icontains=search_prenda)

    search_local = request.GET.get('search_local', '').strip()
    if search_local:
        prendas_qs = prendas_qs.filter(idLocal__Nombre_local__icontains=search_local)

    search_vendedor = request.GET.get('search_vendedor', '').strip()
    if search_vendedor:
        prendas_qs = prendas_qs.filter(idLocal__IdUsuario__nombres__icontains=search_vendedor) | \
                     prendas_qs.filter(idLocal__IdUsuario__apellidos__icontains=search_vendedor)

    talla = request.GET.get('talla', '').strip()
    if talla and talla != 'all':
        prendas_qs = prendas_qs.filter(talla=talla)

    tipo = request.GET.get('tipo', '').strip()
    if tipo and tipo != 'all':
        prendas_qs = prendas_qs.filter(tipoPrenda=tipo)

    material = request.GET.get('material', '').strip()
    if material and material != 'all':
        prendas_qs = prendas_qs.filter(material=material)

    sort = request.GET.get('sort', '').strip()
    if sort == 'price_asc':
        prendas_qs = prendas_qs.order_by('precio')
    elif sort == 'price_desc':
        prendas_qs = prendas_qs.order_by('-precio')
    elif sort == 'newest':
        prendas_qs = prendas_qs.order_by('-fechaPublicacion')
    else:
        prendas_qs = prendas_qs.order_by('nombre')

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        prendas_qs = prendas_qs.filter(precio__gte=min_price)
    if max_price:
        prendas_qs = prendas_qs.filter(precio__lte=max_price)

    # --- PAGINACIÓN (20 items) ---
    paginator = Paginator(prendas_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Conteo seguro de items en el carrito para Clientes y Anónimos
    cart_count = 0
    if rol != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    return render(request, "cardsuni.html", {
        "nombre": nombre,
        "rol": rol,
        "page_obj": page_obj,
        "search_prenda": search_prenda,
        "search_local": search_local,
        "search_vendedor": search_vendedor,
        "talla_sel": talla,
        "tipo_sel": tipo,
        "material_sel": material,
        "sort_sel": sort,
        "min_price": min_price,
        "max_price": max_price,
        "prenda_talla_choices": Prendas.TALLA_CHOICES,
        "prenda_material_choices": Prendas.MATERIAL_CHOICES,
        "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
        "cart_count": cart_count,
        "pedidos_pendientes_count": pedidos_pendientes_count,
    })

def detalle_prenda(request, id_prenda):
    prenda = get_object_or_404(Prendas, pk=id_prenda, activo=True)
    recomendados = Prendas.objects.filter(idLocal__EstaActivo=True, activo=True).exclude(pk=id_prenda).order_by('?')[:15]

    # Conteo seguro para Clientes y Anónimos
    cart_count = 0
    if request.session.get("usuario_rol") != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    return render(request, "detalleuniforme.html", {"prenda": prenda, "recomendados": recomendados, "cart_count": cart_count})

def agregar_carrito(request, id_prenda):
    if "usuario_id" not in request.session:
        messages.warning(request, "Debes iniciar sesión para agregar productos al carrito 🔒")
        return redirect('login')

    if request.session.get("usuario_rol") != "Cliente":
        messages.error(request, "Solo los clientes pueden añadir productos al carrito 🚫")
        return redirect(request.META.get('HTTP_REFERER', reverse('catalogo_prendas')))

    # Cambiamos carrito a diccionario para soportar cantidades: {id_prenda: cantidad}
    carrito = request.session.get('carrito', {})
    if not isinstance(carrito, dict): carrito = {}

    id_str = str(id_prenda)
    cantidad = int(request.POST.get('cantidad', 1))

    if id_str in carrito:
        messages.info(request, "Ya tienes este producto en el carrito")
    else:
        carrito[id_str] = cantidad
        messages.success(request, "¡Añadido al carrito con éxito!")

    request.session['carrito'] = carrito
    request.session.modified = True
    
    return redirect(request.META.get('HTTP_REFERER', reverse('catalogo_prendas')))

def eliminar_del_carrito(request, id_prenda):
    if 'carrito' in request.session:
        carrito = request.session['carrito']
        id_str = str(id_prenda)
        if isinstance(carrito, dict) and id_str in carrito:
            del carrito[id_str]
        elif isinstance(carrito, list) and id_prenda in carrito:
            carrito.remove(id_prenda)
            
        request.session.modified = True
        messages.success(request, "Prenda eliminada del carrito correctamente 🗑️")
    return redirect('ver_carrito')

def actualizar_cantidad_carrito(request, id_prenda):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nueva_cantidad = int(data.get('cantidad', 1))
            carrito = request.session.get('carrito', {})
            id_str = str(id_prenda)

            if id_str in carrito:
                prenda = get_object_or_404(Prendas, pk=id_prenda)
                # Validamos que no exceda el stock
                if nueva_cantidad > prenda.stock: nueva_cantidad = prenda.stock
                if nueva_cantidad < 1: nueva_cantidad = 1

                carrito[id_str] = nueva_cantidad
                request.session['carrito'] = carrito
                request.session.modified = True
                
                return JsonResponse({'status': 'success', 'cantidad': nueva_cantidad})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

def ver_carrito(request):
    # Solo bloqueamos a los Vendedores
    if request.session.get("usuario_rol") == "Vendedor":
        messages.error(request, "Los vendedores no pueden gestionar carritos.")
        return redirect('landing')

    carrito = request.session.get('carrito', {})
    if not isinstance(carrito, dict): 
        # Migración segura si antes era una lista
        prendas_ids = carrito
        carrito = {str(pid): 1 for pid in prendas_ids}
        request.session['carrito'] = carrito

    items = []
    total_general = 0
    
    prendas_qs = Prendas.objects.filter(idPrenda__in=carrito.keys())
    
    for p in prendas_qs:
        cant = carrito.get(str(p.idPrenda), 1)
        subtotal = p.precio * cant
        total_general += subtotal
        items.append({
            'obj': p,
            'cantidad': cant,
            'subtotal': subtotal
        })

    return render(request, "carrito.html", {
        "items": items, 
        "total": total_general, 
        "cart_count": sum(carrito.values())
    })

@transaction.atomic
def procesar_pago(request):
    if "usuario_id" not in request.session:
        return redirect('login')
    
    if request.method == "POST":
        usuario_id = request.session.get("usuario_id")
        carrito = request.session.get('carrito', {})
        
        if request.session.get("usuario_rol") == "Vendedor":
            messages.error(request, "Acceso denegado. Los vendedores no pueden procesar pagos.")
            return redirect('landing')

        if not carrito:
            messages.error(request, "El carrito está vacío 🛒")
            return redirect('catalogo_prendas')

    
        # 1. Obtener seleccionados del formulario.
        selected_ids = request.POST.getlist('seleccionados')
        if not selected_ids:
            messages.warning(request, "⚠️ Por favor, selecciona al menos un producto para pagar.")
            return redirect('ver_carrito')


        # Corrección Abono: Convertir a int/decimal elimina ceros a la izquierda automáticamente
        try:
            abono_total = Decimal(str(request.POST.get('abono_pago', '0')).strip())
        except:
            abono_total = Decimal(0)
        
        # Calcular total real del pedido
        total_p = Decimal(0)
        prendas_list = []
        
        # 2. Filtrar el proceso: Solo iteramos sobre los IDs seleccionados
        for p_id in selected_ids:
            cant = carrito.get(p_id)
            if not cant: continue
            
            prenda = get_object_or_404(Prendas, pk=p_id)
            
            # REGLA DE NEGOCIO: Validar Stock real en el momento del pago
            if not prenda.activo or prenda.stock < cant:
                messages.error(request, f"Lo sentimos, solo quedan {prenda.stock} unidades de {prenda.nombre} 😔")
                return redirect('ver_carrito')

            subtotal = prenda.precio * cant
            total_p += subtotal
            prendas_list.append((prenda, cant, subtotal))
def ver_pedido(request, id_pedido):
    usuario_id = request.session.get("usuario_id")
    pedido = get_object_or_404(Pedido, idPedido=id_pedido, usuario_id=usuario_id)
    # Ahora el estado es directo
    estado_actual = pedido.estado
    detalles = DetallePedido.objects.filter(pedido=pedido)
    
    # Calculamos totales desde los detalles ya que se movieron del modelo Pedido
    totales = detalles.aggregate(
        total=models.Sum('total_pedido'), 
        abono=models.Sum('total_abono')
    )
    total_pedido = totales['total'] or 0
    total_abono = totales['abono'] or 0
    saldo_pendiente = total_pedido - total_abono
    
    return render(request, "pedido.html", {
        "pedido": pedido, 
        "detalles": detalles,
        "total_pedido": total_pedido,
        "total_abono": total_abono,
        "saldo_pendiente": saldo_pendiente,
        "estado": estado_actual
    })

def mis_pedidos(request):
    if "usuario_id" not in request.session:
        return redirect('login')
    
    usuario_id = request.session.get("usuario_id")
    rol = request.session.get("usuario_rol")
    
    # Optimizamos la consulta anotando información clave para que el historial sea "bonito" y rápido
    # Obtenemos el nombre de la primera prenda, el local y el vendedor del pedido para mostrar en el resumen
    primer_uniforme = DetallePedido.objects.filter(pedido=OuterRef('pk')).values('prenda__nombre')[:1]
    primer_local = DetallePedido.objects.filter(pedido=OuterRef('pk')).values('prenda__idLocal__Nombre_local')[:1]
    primer_vendedor = DetallePedido.objects.filter(pedido=OuterRef('pk')).values('prenda__idLocal__IdUsuario__nombres')[:1]

    # Anotamos los totales acumulados desde los detalles para poder filtrar y mostrar
    pedidos_qs = Pedido.objects.all().annotate(
        total_acumulado=models.Sum('detallepedido__total_pedido'),
        abono_acumulado=models.Sum('detallepedido__total_abono')
    ).select_related(
        'estado',
        'usuario'
    ).prefetch_related(
        'detallepedido_set__prenda__idLocal__IdUsuario',
        'detallepedido_set__prenda'
    ).annotate(
        nombre_principal=Subquery(primer_uniforme),
        local_principal=Subquery(primer_local),
        vendedor_principal=Subquery(primer_vendedor)
    )

    if rol == "Vendedor":
        # El vendedor ve pedidos que contienen prendas de sus locales
        pedidos_qs = pedidos_qs.filter(detallepedido__prenda__idLocal__IdUsuario_id=usuario_id).distinct()
    elif rol == "Administrador":
        pass # El admin ve todos
    else:
        pedidos_qs = pedidos_qs.filter(usuario_id=usuario_id)
    
    # --- FILTROS DE HISTORIAL ---
    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        pedidos_qs = pedidos_qs.filter(estado__estado_pedido=estado_filtro)

    # --- FILTRO POR ESTADO DE PAGO (Saldado o con saldo pendiente) ---
    pago_status = request.GET.get('pago_status')
    if pago_status == 'pagado':
        pedidos_qs = pedidos_qs.filter(abono_acumulado__gte=models.F('total_acumulado'))
    elif pago_status == 'pendiente':
        pedidos_qs = pedidos_qs.filter(abono_acumulado__lt=models.F('total_acumulado'))

    # --- FILTROS POR CARACTERÍSTICAS DE PRENDAS (Talla y Tipo) ---
    talla_filtro = request.GET.get('talla')
    if talla_filtro and talla_filtro != 'all':
        pedidos_qs = pedidos_qs.filter(detallepedido__prenda__talla=talla_filtro).distinct()

    tipo_filtro = request.GET.get('tipo_prenda')
    if tipo_filtro and tipo_filtro != 'all':
        pedidos_qs = pedidos_qs.filter(detallepedido__prenda__tipoPrenda=tipo_filtro).distinct()

    # --- FILTRO POR FECHAS ---
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    if fecha_inicio:
        pedidos_qs = pedidos_qs.filter(fecha_pedido__date__gte=fecha_inicio)
    if fecha_fin:
        pedidos_qs = pedidos_qs.filter(fecha_pedido__date__lte=fecha_fin)

    # --- FILTRO POR PRECIO (TOTAL) ---
    min_total = request.GET.get('min_total')
    max_total = request.GET.get('max_total')
    if min_total:
        pedidos_qs = pedidos_qs.filter(total_acumulado__gte=min_total)
    if max_total:
        pedidos_qs = pedidos_qs.filter(total_acumulado__lte=max_total)

    # --- FILTRO POR ID DE PEDIDO ---
    pedido_id = request.GET.get('pedido_id')
    if pedido_id:
        pedidos_qs = pedidos_qs.filter(idPedido=pedido_id)

    # --- FILTRO INTERACTIVO (Local, Vendedor o Nombre del Uniforme) ---
    q = request.GET.get('q', '').strip()
    if q:
        pedidos_qs = pedidos_qs.filter(
            models.Q(detallepedido__prenda__idLocal__Nombre_local__icontains=q) |
            models.Q(detallepedido__prenda__nombre__icontains=q) |
            models.Q(detallepedido__prenda__idLocal__IdUsuario__nombres__icontains=q)
        ).distinct()

    pedidos_qs = pedidos_qs.order_by('-fecha_pedido')
    
    context = {
        "pedidos": pedidos_qs,
        "estado_filtro": estado_filtro,
        "search_q": q,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "min_total": min_total,
        "max_total": max_total,
        "pedido_id": pedido_id,
        "pago_status_sel": pago_status,
        "talla_sel": talla_filtro,
        "tipo_sel": tipo_filtro,
        "estados_choices": EstadoPedido.ESTADO_CHOICES,
        "talla_choices": Prendas.TALLA_CHOICES,
        "tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
    }
    return render(request, "mis_pedidos.html", context)

def explorar_locales(request):
    # Filtramos solo locales activos para los clientes
    locales_qs = Local.objects.filter(EstaActivo=True).select_related('IdUsuario')

    # Filtros
    search_nombre = request.GET.get('nombre', '').strip()
    search_ubicacion = request.GET.get('ubicacion', '').strip()
    search_vendedor = request.GET.get('vendedor', '').strip()
    search_apertura = request.GET.get('apertura', '').strip()

    if search_nombre:
        locales_qs = locales_qs.filter(Nombre_local__icontains=search_nombre)
    
    if search_ubicacion:
        locales_qs = locales_qs.filter(Ubicacion_direccion__icontains=search_ubicacion)

    if search_vendedor:
        locales_qs = locales_qs.filter(
            models.Q(IdUsuario__nombres__icontains=search_vendedor) |
            models.Q(IdUsuario__apellidos__icontains=search_vendedor)
        )

    if search_apertura:
        locales_qs = locales_qs.filter(Horaapertura__icontains=search_apertura)

    # Paginación para 20 locales por página
    paginator = Paginator(locales_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Conteo seguro para Clientes y Anónimos
    cart_count = 0
    if request.session.get("usuario_rol") != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    return render(request, "localuni.html", {
        "locales": page_obj,
        "search_nombre": search_nombre,
        "search_ubicacion": search_ubicacion,
        "search_vendedor": search_vendedor,
        "search_apertura": search_apertura,
        "cart_count": cart_count
    })

def ver_productos_local(request, id_local):
    local = get_object_or_404(Local, IdLocal=id_local, EstaActivo=True)
    
    prendas_qs = Prendas.objects.filter(idLocal=local, activo=True).select_related('idLocal', 'idLocal__IdUsuario')

    # --- FILTROS ---
    search_prenda = request.GET.get('search_prenda', '').strip()
    if search_prenda:
        prendas_qs = prendas_qs.filter(nombre__icontains=search_prenda)

    talla = request.GET.get('talla', '').strip()
    if talla and talla != 'all':
        prendas_qs = prendas_qs.filter(talla=talla)

    tipo = request.GET.get('tipo', '').strip()
    if tipo and tipo != 'all':
        prendas_qs = prendas_qs.filter(tipoPrenda=tipo)

    material = request.GET.get('material', '').strip()
    if material and material != 'all':
        prendas_qs = prendas_qs.filter(material=material)

    sort = request.GET.get('sort', '').strip()
    if sort == 'price_asc':
        prendas_qs = prendas_qs.order_by('precio')
    elif sort == 'price_desc':
        prendas_qs = prendas_qs.order_by('-precio')
    elif sort == 'newest':
        prendas_qs = prendas_qs.order_by('-fechaPublicacion')
    else:
        prendas_qs = prendas_qs.order_by('nombre')

    # --- PAGINACIÓN (20 items) ---
    paginator = Paginator(prendas_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Conteo seguro para Clientes y Anónimos
    cart_count = 0
    if request.session.get("usuario_rol") != "Vendedor":
        carrito = request.session.get('carrito', {})
        if isinstance(carrito, dict):
            cart_count = sum(carrito.values())
        else:
            cart_count = len(carrito) if isinstance(carrito, list) else 0

    return render(request, "localproduc.html", {
        "local": local,
        "page_obj": page_obj,
        "search_prenda": search_prenda,
        "talla_sel": talla,
        "tipo_sel": tipo,
        "material_sel": material,
        "sort_sel": sort,
        "prenda_talla_choices": Prendas.TALLA_CHOICES,
        "prenda_material_choices": Prendas.MATERIAL_CHOICES,
        "prenda_tipo_choices": Prendas.TIPO_PRENDA_CHOICES,
        "cart_count": cart_count,
    })

def actualizar_fecha_entrega(request, id_pedido):
    if request.method == "POST":
        pedido = get_object_or_404(Pedido, idPedido=id_pedido, usuario_id=request.session.get("usuario_id"))
        fecha = request.POST.get("fecha_entrega")
        if fecha:
            pedido.fecha_entrega = fecha
            pedido.save()
            messages.success(request, "Fecha de recogida programada correctamente 📅")
    return redirect('ver_pedido', id_pedido=id_pedido)

def calificar_local(request, id_local):
    if request.session.get("usuario_rol") == "Vendedor":
        messages.error(request, "Los vendedores no pueden calificar locales 🚫")
        return redirect(request.META.get('HTTP_REFERER', 'landing'))

    if request.method == "POST" and "usuario_id" in request.session:
        local = get_object_or_404(Local, IdLocal=id_local)
        comentario = request.POST.get("comentario")
        valoracion = request.POST.get("valoracion")
        
        CalificacionPedido.objects.create(
            locales=local,
            usuario_id=request.session.get("usuario_id"),
            comentario=comentario,
            valoracion=valoracion
        )
        messages.success(request, "¡Gracias por calificar el local! ⭐")
    return redirect(request.META.get('HTTP_REFERER', 'landing'))