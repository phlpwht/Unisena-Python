from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from usuario.models import Usuario, Rol
from locales.models import Local
from uniformes.models import Prendas, Pedido, EstadoPedido, DetallePedido
from decimal import Decimal
from django.utils import timezone
import json

class UniformesBusinessLogicTests(TestCase):
    def setUp(self):
        # Configuración de roles y usuarios
        self.rol_vendedor = Rol.objects.create(id=1, nombre_rol="Vendedor")
        self.rol_cliente = Rol.objects.create(id=2, nombre_rol="Cliente")
        
        self.vendedor = Usuario.objects.create(
            correo="vendedor@test.com",
            nombres="Juan",
            apellidos="Vendedor",
            rol=self.rol_vendedor,
            fecha_nacimiento=timezone.now().date(),
            num_identificacion="123456789",
            tipo_identificacion='CC'
        )
        
        self.cliente = Usuario.objects.create(
            correo="cliente@test.com",
            nombres="Maria",
            apellidos="Cliente",
            rol=self.rol_cliente,
            fecha_nacimiento=timezone.now().date(),
            num_identificacion="987654321",
            tipo_identificacion='CC'
        )
        
        # Configuración de local y producto
        self.local = Local.objects.create(
            IdUsuario=self.vendedor,
            Nombre_local="Tienda Escolar Test",
            EstaActivo=True
        )
        
        self.prenda = Prendas.objects.create(
            idLocal=self.local,
            nombre="Chaqueta Deportiva",
            precio=Decimal("100000.00"),
            stock=10,
            talla="M",
            material="Malla",
            tipoPrenda="unidad",
            activo=True
        )
        
        # Estado inicial requerido para pedidos
        self.estado_pendiente = EstadoPedido.objects.create(estado_pedido='PENDIENTE')

    def test_catalogo_visibilidad(self):
        """Verifica que el catálogo cargue correctamente los productos activos."""
        response = self.client.get(reverse('catalogo_prendas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.prenda.nombre)

    def test_restriccion_rol_carrito(self):
        """Verifica que un vendedor no pueda añadir productos al carrito (solo clientes)."""
        session = self.client.session
        session['usuario_id'] = self.vendedor.id
        session['usuario_rol'] = "Vendedor"
        session.save()
        
        response = self.client.post(reverse('agregar_carrito', args=[self.prenda.idPrenda]), {'cantidad': 1})
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Solo los clientes pueden añadir productos" in str(m) for m in messages))

    def test_validacion_abono_minimo(self):
        """Prueba la regla de negocio: el abono debe ser al menos el 20% del total."""
        # Simular sesión de cliente con producto en carrito
        session = self.client.session
        session['usuario_id'] = self.cliente.id
        session['usuario_rol'] = "Cliente"
        session['carrito'] = {str(self.prenda.idPrenda): 1}
        session.save()
        
        # Total es 100.000, el 20% es 20.000. Intentamos con 15.000.
        response = self.client.post(reverse('procesar_pago'), {
            'seleccionados': [str(self.prenda.idPrenda)],
            'abono_pago': '15000'
        })
        
        # No debe crearse el pedido
        self.assertEqual(Pedido.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("abono mínimo" in str(m).lower() for m in messages))

    def test_procesar_pago_exitoso(self):
        """Verifica la creación correcta de pedido y detalles con abono válido."""
        session = self.client.session
        session['usuario_id'] = self.cliente.id
        session['usuario_rol'] = "Cliente"
        session['carrito'] = {str(self.prenda.idPrenda): 1}
        session.save()
        
        # Abono de 30.000 (30%)
        response = self.client.post(reverse('procesar_pago'), {
            'seleccionados': [str(self.prenda.idPrenda)],
            'abono_pago': '30000'
        })
        
        self.assertEqual(Pedido.objects.count(), 1)
        pedido = Pedido.objects.first()
        detalle = DetallePedido.objects.get(pedido=pedido)
        self.assertEqual(detalle.total_abono, Decimal('30000'))
        
        # El carrito debe quedar vacío para ese producto
        self.assertNotIn(str(self.prenda.idPrenda), self.client.session['carrito'])

    def test_validar_stock_insuficiente(self):
        """Verifica que no se pueda añadir más cantidad de la disponible en stock."""
        # La prenda tiene stock 10, intentamos añadir 15
        # 1. Necesitamos que el producto esté en el carrito para poder actualizar su cantidad
        session = self.client.session
        session['carrito'] = {str(self.prenda.idPrenda): 1}
        session.save()

        # 2. La prenda tiene stock 10, intentamos actualizar a 15
        response = self.client.post(reverse('actualizar_cantidad_carrito', args=[self.prenda.idPrenda]), 
                                    data=json.dumps({"cantidad": 15}), 
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['cantidad'], 10)