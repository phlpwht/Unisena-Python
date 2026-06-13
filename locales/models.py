from django.db import models
from usuario.models import Usuario  # o ajusta el import según tu app
from django.utils.timezone import now

class Local(models.Model):
    IdLocal = models.AutoField(primary_key=True)
    #RELACIÓN CON USUARIO
    IdUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='locales')  # opcional pero recomendado
    Nombre_local = models.CharField(max_length=100)
    Descripcion = models.TextField()
    Ubicacion_direccion = models.CharField(max_length=255)
    Imagen = models.ImageField(upload_to='locales/', null=True, blank=True)
    Horaapertura = models.TimeField(null=True, blank=True)
    HoraCierre = models.TimeField(null=True, blank=True)
    EstaActivo = models.BooleanField(default=True)
    Numero = models.CharField(max_length=10, null=True, blank=True)  

    def __str__(self):
        return self.Nombre_local

class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    motivo = models.TextField(null=True, blank=True)
    leida = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=now)
    tipo = models.CharField(max_length=50, default='info') # info, alerta, exito, error