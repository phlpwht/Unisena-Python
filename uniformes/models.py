from django.db import models
from locales.models import Local #ajusta el import según tu app
from usuario.models import Usuario  #ajusta el import según tu app
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Prendas(models.Model):
    idPrenda = models.AutoField(primary_key=True)
    idLocal = models.ForeignKey(Local, on_delete=models.CASCADE, related_name='prendas') # Campo para almacenar el ID del local al que pertenece la prenda   
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='prendas/', blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    TALLA_CHOICES = [
        ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
    ]
    talla = models.CharField(
        max_length=3,
        choices=TALLA_CHOICES
    )
    MATERIAL_CHOICES = [
        ('Algodon', 'Algodón'),
        ('Malla', 'Malla'),
    ]
    material = models.CharField(max_length=50, choices=MATERIAL_CHOICES)
    stock = models.IntegerField(validators=[MinValueValidator(1)])
    activo = models.BooleanField(default=True)
    fechaPublicacion = models.DateTimeField(auto_now_add=True)
    TIPO_PRENDA_CHOICES = [
        ('unidad', 'Unidad'), ('completa', 'Prenda Completa'),
    ]
    tipoPrenda = models.CharField(
        max_length=50,
        choices=TIPO_PRENDA_CHOICES
    )
    def __str__(self):  
        return self.nombre
    
class Pedido(models.Model):
    idPedido = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='pedidos', null=True)
    num_pedido_cliente = models.PositiveIntegerField(default=1, help_text="Secuencia de pedido para el cliente")
    estado = models.ForeignKey('EstadoPedido', on_delete=models.CASCADE, related_name='pedidos')
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return "Pedido"

class EstadoPedido(models.Model):
    id_estado = models.AutoField(primary_key=True)
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado'),
    ]
    estado_pedido = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='PENDIENTE')

    def __str__(self):
        return self.estado_pedido
    
class DetallePedido(models.Model):
    idDetalle = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    prenda = models.ForeignKey(Prendas, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    talla = models.CharField(max_length=3)
    total_pedido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_abono = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class PagoPedido(models.Model):
    idPago = models.AutoField(primary_key=True)
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)

    METODO_CHOICES = [('EFECTIVO', 'Efectivo'), ('TRANSFERENCIA', 'Transferencia')]
    metodo_pago = models.CharField(max_length=50, choices=METODO_CHOICES)
    
    ESTADO_PAGO_CHOICES = [('PAGADO', 'Pagado'), ('PENDIENTE', 'Pendiente')]
    estado_pago = models.CharField(max_length=50, choices=ESTADO_PAGO_CHOICES)
    
class CalificacionPedido(models.Model):
    id_calificacion = models.AutoField(primary_key=True)
    locales = models.ForeignKey(Local, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True)
    comentario = models.CharField(max_length=500)
    valoracion = models.IntegerField()
    
