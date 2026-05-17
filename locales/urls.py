from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_vendedor, name='dashboard_vendedor'),
    path('lista/', views.lista_locales, name='lista_locales'),
    path('crear/', views.crear_local, name='crear_local'),
    path('editar/<int:id>/', views.editar_local, name='editar_local'),
    path('eliminar/<int:id>/', views.eliminar_local, name='eliminar_local'),
    path('administrar/', views.administrar_locales, name='administrar_locales'),
    path('detalle/<int:id>/', views.detalle_local, name='detalle_local'),
    path('toggle-activo/<int:id>/', views.toggle_activo_local, name='toggle_activo_local'),
    path('prenda/<int:id_prenda>/movimientos/', views.ver_movimientos_prenda, name='ver_movimientos_prenda'),
    path('pedido/<int:id_local>/<int:id_pedido>/', views.detalle_pedido_vendedor, name='detalle_pedido_vendedor'),
    path('exportar-excel/<int:id_local>/', views.exportar_ventas_excel, name='exportar_ventas_excel'),
    path('reporte-pdf/<int:id_local>/', views.ver_reporte_pdf, name='ver_reporte_pdf'),
    path('previa-excel/<int:id_local>/', views.previa_excel_local, name='previa_excel_local'),
]