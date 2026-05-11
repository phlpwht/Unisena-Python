
from django.db import models
from uniformes.models import Prendas, DetallePedido  # relaciones correctas según tu BD


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]

    idMovimiento = models.AutoField(primary_key=True)
    idPrenda = models.ForeignKey(Prendas, on_delete=models.CASCADE, related_name='movimientos')
    idDetalle = models.ForeignKey(DetallePedido, on_delete=models.SET_NULL, null=True, blank=True)
    tipoMovimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipoMovimiento} {self.cantidad} de {self.idPrenda.nombre} en {self.fecha}"