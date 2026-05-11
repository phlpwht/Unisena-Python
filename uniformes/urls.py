from django.urls import path
from . import views
from locales import views as locales_views

urlpatterns = [
    # Crear prenda nueva
    path('crear_prenda/<int:id_local>/', views.crear_prenda, name='crear_prenda'),
    # Editar prenda existente
    path('editar_prenda/<int:id_prenda>/', views.editar_prenda, name='editar_prenda'),
    # Eliminar prenda
    path('eliminar_prenda/<int:id_prenda>/', views.eliminar_prenda, name='eliminar_prenda'),
    # Carga masiva de prendas
    path('bulk_upload/<int:id_local>/', views.bulk_upload_prendas, name='bulk_upload_prendas'),
    # Eliminar prendas masivo
    path('eliminar_masivo/<int:id_local>/', views.eliminar_prendas_masivo, name='eliminar_prendas_masivo'),
    
    # 🛒 CATÁLOGO Y CARRITO (MOVIDOS AQUÍ)
    path('catalogo/', views.catalogo_prendas, name='catalogo_prendas'),
    path('uniforme/<int:id_prenda>/', views.detalle_prenda, name='detalle_prenda'),
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<int:id_prenda>/', views.agregar_carrito, name='agregar_carrito'), # Ahora maneja cantidades
    path('carrito/eliminar/<int:id_prenda>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('pedido/procesar/', views.procesar_pago, name='procesar_pago'),
    path('pedido/<int:id_pedido>/', views.ver_pedido, name='ver_pedido'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),

    # 🏢 EXPLORAR LOCALES
    path('explorar-locales/', views.explorar_locales, name='explorar_locales'),
    # 🛍️ VER PRODUCTOS DE UN LOCAL ESPECÍFICO (PARA CLIENTES)
    path('locales/<int:id_local>/productos/', views.ver_productos_local, name='ver_productos_local'),

    # 📦 PEDIDOS DEL LOCAL (VISTA VENDEDOR)
    path('pedido/<int:id_pedido>/fecha-entrega/', views.actualizar_fecha_entrega, name='actualizar_fecha_entrega'),
    path('local/<int:id_local>/calificar/', views.calificar_local, name='calificar_local'),
    path('locales/<int:id_local>/pedido/<int:id_pedido>/detalle/', locales_views.detalle_pedido_vendedor, name='detalle_pedido_vendedor'),
]